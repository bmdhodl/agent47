import { NextResponse } from "next/server";
import sql from "@/lib/db";
import { hashApiKey } from "@/lib/api-key";
import { eventSchema } from "@/lib/validation";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";

export async function POST(request: Request) {
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
  const keyRows = await sql`
    SELECT team_id FROM api_keys
    WHERE key_hash = ${keyHash} AND revoked_at IS NULL
  `;

  if (keyRows.length === 0) {
    return NextResponse.json(
      { error: "Invalid or revoked API key" },
      { status: 401 },
    );
  }

  const teamId = keyRows[0].team_id;

  // 3. Check usage limits
  const teamRows = await sql`
    SELECT plan FROM teams WHERE id = ${teamId}
  `;

  const plan = PLANS[(teamRows[0]?.plan as PlanName) ?? "free"] ?? PLANS.free;
  const month = new Date().toISOString().slice(0, 7);

  const usageRows = await sql`
    SELECT event_count FROM usage
    WHERE team_id = ${teamId} AND month = ${month}
  `;

  const currentCount = usageRows.length > 0 ? Number(usageRows[0].event_count) : 0;

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
  const validEvents: Array<{
    team_id: string;
    trace_id: string;
    span_id: string;
    parent_id: string | null;
    kind: string;
    phase: string;
    name: string;
    ts: number;
    duration_ms: number | null;
    data: Record<string, unknown>;
    error: { type: string; message: string } | null;
    service: string;
  }> = [];
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
    validEvents.push({
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

  if (validEvents.length === 0) {
    return NextResponse.json(
      { error: "No valid events", details: errors },
      { status: 400 },
    );
  }

  // 6. Batch insert events
  for (const ev of validEvents) {
    await sql`
      INSERT INTO events (team_id, trace_id, span_id, parent_id, kind, phase, name, ts, duration_ms, data, error, service)
      VALUES (${ev.team_id}, ${ev.trace_id}, ${ev.span_id}, ${ev.parent_id}, ${ev.kind}, ${ev.phase}, ${ev.name}, ${ev.ts}, ${ev.duration_ms}, ${JSON.stringify(ev.data)}::jsonb, ${ev.error ? JSON.stringify(ev.error) : null}::jsonb, ${ev.service})
    `;
  }

  // 7. Increment usage counter
  await sql`
    INSERT INTO usage (team_id, month, event_count)
    VALUES (${teamId}, ${month}, ${validEvents.length})
    ON CONFLICT (team_id, month)
    DO UPDATE SET event_count = usage.event_count + ${validEvents.length}
  `;

  return NextResponse.json({
    accepted: validEvents.length,
    rejected: errors.length,
    errors: errors.length > 0 ? errors : undefined,
  });
}
