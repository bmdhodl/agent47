import sql from "@/lib/db";

export interface TraceRow {
  trace_id: string;
  service: string;
  root_name: string;
  event_count: number;
  error_count: number;
  duration_ms: number | null;
  started_at: string;
  api_key_name: string | null;
  api_key_prefix: string | null;
}

export interface EventRow {
  id: number;
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
  created_at: string;
  api_key_name: string | null;
  api_key_prefix: string | null;
}

export async function getTraceList(teamId: string): Promise<TraceRow[]> {
  const rows = await sql`
    SELECT
      e.trace_id,
      MIN(e.service) as service,
      MIN(e.name) FILTER (WHERE e.parent_id IS NULL AND e.phase = 'start') as root_name,
      COUNT(*)::int as event_count,
      COUNT(*) FILTER (WHERE e.error IS NOT NULL)::int as error_count,
      MAX(e.duration_ms) as duration_ms,
      MIN(e.created_at) as started_at,
      MIN(ak.name) as api_key_name,
      MIN(ak.prefix) as api_key_prefix
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId}
    GROUP BY e.trace_id
    ORDER BY MIN(e.created_at) DESC
    LIMIT 100
  `;

  return rows as unknown as TraceRow[];
}

export async function getTraceEvents(
  teamId: string,
  traceId: string,
): Promise<EventRow[]> {
  const rows = await sql`
    SELECT e.id, e.trace_id, e.span_id, e.parent_id, e.kind, e.phase, e.name, e.ts,
           e.duration_ms, e.data, e.error, e.service, e.created_at,
           ak.name as api_key_name, ak.prefix as api_key_prefix
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId} AND e.trace_id = ${traceId}
    ORDER BY e.ts ASC
  `;

  return rows as unknown as EventRow[];
}

export async function getUsageStats(teamId: string) {
  const month = new Date().toISOString().slice(0, 7);

  const rows = await sql`
    SELECT event_count FROM usage
    WHERE team_id = ${teamId} AND month = ${month}
  `;

  return {
    currentMonth: month,
    eventCount: rows.length > 0 ? Number(rows[0].event_count) : 0,
  };
}

export async function getAlerts(teamId: string): Promise<EventRow[]> {
  const rows = await sql`
    SELECT e.id, e.trace_id, e.span_id, e.parent_id, e.kind, e.phase, e.name, e.ts,
           e.duration_ms, e.data, e.error, e.service, e.created_at,
           ak.name as api_key_name, ak.prefix as api_key_prefix
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId}
      AND (e.name = 'guard.loop_detected' OR e.name = 'guard.budget_exceeded' OR e.error IS NOT NULL)
    ORDER BY e.created_at DESC
    LIMIT 50
  `;

  return rows as unknown as EventRow[];
}
