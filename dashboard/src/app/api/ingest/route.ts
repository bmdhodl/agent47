import { NextResponse } from "next/server";
import sql from "@/lib/db";
import { hashApiKey } from "@/lib/api-key";
import { eventSchema } from "@/lib/validation";
import { PLANS } from "@/lib/plans";
import type { PlanName } from "@/lib/plans";
import { rateLimit, getClientIp } from "@/lib/rate-limit";

export async function POST(request: Request) {
  // Rate limit: 100 requests per minute per IP
  const ip = getClientIp(request);
  const rl = rateLimit(`ingest:${ip}`, 100, 60_000);
  if (!rl.ok) {
    return NextResponse.json({ error: "Too many requests" }, { status: 429 });
  }

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
    SELECT id, team_id FROM api_keys
    WHERE key_hash = ${keyHash} AND revoked_at IS NULL
  `;

  if (keyRows.length === 0) {
    return NextResponse.json(
      { error: "Invalid or revoked API key" },
      { status: 401 },
    );
  }

  const teamId = keyRows[0].team_id;
  const apiKeyId = keyRows[0].id;

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

  // 4. Parse NDJSON body (limit: 1MB)
  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > 1_048_576) {
    return NextResponse.json(
      { error: "Request body too large (max 1MB)" },
      { status: 413 },
    );
  }

  const body = await request.text();
  if (body.length > 1_048_576) {
    return NextResponse.json(
      { error: "Request body too large (max 1MB)" },
      { status: 413 },
    );
  }

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
    api_key_id: string;
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
      api_key_id: apiKeyId,
    });
  }

  if (validEvents.length === 0) {
    return NextResponse.json(
      { error: "No valid events", details: errors },
      { status: 400 },
    );
  }

  // 6. Batch insert events (single query with unnest)
  const teamIds = validEvents.map(() => teamId);
  const traceIds = validEvents.map((e) => e.trace_id);
  const spanIds = validEvents.map((e) => e.span_id);
  const parentIds = validEvents.map((e) => e.parent_id);
  const kinds = validEvents.map((e) => e.kind);
  const phases = validEvents.map((e) => e.phase);
  const names = validEvents.map((e) => e.name);
  const timestamps = validEvents.map((e) => e.ts);
  const durations = validEvents.map((e) => e.duration_ms);
  const dataArr = validEvents.map((e) => JSON.stringify(e.data));
  const errorArr = validEvents.map((e) =>
    e.error ? JSON.stringify(e.error) : null,
  );
  const services = validEvents.map((e) => e.service);
  const apiKeyIds = validEvents.map((e) => e.api_key_id);

  await sql`
    INSERT INTO events (team_id, trace_id, span_id, parent_id, kind, phase, name, ts, duration_ms, data, error, service, api_key_id)
    SELECT * FROM unnest(
      ${teamIds}::uuid[],
      ${traceIds}::text[],
      ${spanIds}::text[],
      ${parentIds}::text[],
      ${kinds}::text[],
      ${phases}::text[],
      ${names}::text[],
      ${timestamps}::double precision[],
      ${durations}::double precision[],
      ${dataArr}::jsonb[],
      ${errorArr}::jsonb[],
      ${services}::text[],
      ${apiKeyIds}::uuid[]
    )
  `;

  // 7. Increment usage counter (atomic — prevents race condition)
  await sql`
    INSERT INTO usage (team_id, month, event_count)
    VALUES (${teamId}, ${month}, ${validEvents.length})
    ON CONFLICT (team_id, month)
    DO UPDATE SET event_count = usage.event_count + EXCLUDED.event_count
  `;

  return NextResponse.json({
    accepted: validEvents.length,
    rejected: errors.length,
    errors: errors.length > 0 ? errors : undefined,
  });
}
