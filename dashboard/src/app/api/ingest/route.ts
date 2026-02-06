import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase/admin";
import { hashApiKey } from "@/lib/api-key";
import { eventSchema } from "@/lib/validation";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function POST(request: Request) {
  const supabaseAdmin = getSupabaseAdmin();

  // 1. Extract Bearer token
  const auth = request.headers.get("authorization");
  if (!auth?.startsWith("Bearer ")) {
    return NextResponse.json(
      { error: "Missing or invalid Authorization header" },
      { status: 401 },
    );
  }

  const rawKey = auth.slice(7);
  const keyHash = hashApiKey(rawKey);

  // 2. Look up API key
  const { data: keyRow } = await supabaseAdmin
    .from("api_keys")
    .select("team_id")
    .eq("key_hash", keyHash)
    .is("revoked_at", null)
    .single();

  if (!keyRow) {
    return NextResponse.json(
      { error: "Invalid or revoked API key" },
      { status: 401 },
    );
  }

  const teamId = keyRow.team_id;

  // 3. Check usage limits
  const { data: team } = await supabaseAdmin
    .from("teams")
    .select("plan")
    .eq("id", teamId)
    .single();

  const plan = PLANS[(team?.plan as PlanName) ?? "free"] ?? PLANS.free;
  const month = new Date().toISOString().slice(0, 7); // YYYY-MM

  const { data: usage } = await supabaseAdmin
    .from("usage")
    .select("event_count")
    .eq("team_id", teamId)
    .eq("month", month)
    .single();

  const currentCount = usage?.event_count ?? 0;

  // 4. Parse NDJSON body
  const body = await request.text();
  const lines = body
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return NextResponse.json({ error: "Empty body" }, { status: 400 });
  }

  if (currentCount + lines.length > plan.max_events) {
    return NextResponse.json(
      {
        error: "Monthly event limit exceeded",
        limit: plan.max_events,
        current: currentCount,
      },
      { status: 429 },
    );
  }

  // 5. Validate and collect events
  const rows: Array<Record<string, unknown>> = [];
  const errors: Array<{ line: number; error: string }> = [];

  for (let i = 0; i < lines.length; i++) {
    let parsed: unknown;
    try {
      parsed = JSON.parse(lines[i]);
    } catch {
      errors.push({ line: i, error: "Invalid JSON" });
      continue;
    }

    const result = eventSchema.safeParse(parsed);
    if (!result.success) {
      errors.push({
        line: i,
        error: result.error.issues[0]?.message ?? "Validation failed",
      });
      continue;
    }

    const ev = result.data;
    rows.push({
      team_id: teamId,
      trace_id: ev.trace_id,
      span_id: ev.span_id,
      parent_id: ev.parent_id,
      kind: ev.kind,
      phase: ev.phase,
      name: ev.name,
      ts: ev.ts,
      duration_ms: ev.duration_ms,
      data: ev.data,
      error: ev.error,
      service: ev.service,
    });
  }

  if (rows.length === 0) {
    return NextResponse.json(
      { error: "No valid events", details: errors },
      { status: 400 },
    );
  }

  // 6. Batch insert
  const { error: insertError } = await supabaseAdmin
    .from("events")
    .insert(rows);

  if (insertError) {
    return NextResponse.json(
      { error: "Insert failed", details: insertError.message },
      { status: 500 },
    );
  }

  // 7. Increment usage counter
  await supabaseAdmin.rpc("increment_usage", {
    p_team_id: teamId,
    p_month: month,
    p_count: rows.length,
  });

  return NextResponse.json({
    accepted: rows.length,
    rejected: errors.length,
    errors: errors.length > 0 ? errors : undefined,
  });
}
