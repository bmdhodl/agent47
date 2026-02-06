import sql from "@/lib/db";

export interface TraceRow {
  trace_id: string;
  service: string;
  root_name: string;
  event_count: number;
  error_count: number;
  duration_ms: number | null;
  started_at: string;
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
}

export async function getTraceList(teamId: string): Promise<TraceRow[]> {
  const rows = await sql`
    SELECT
      trace_id,
      MIN(service) as service,
      MIN(name) FILTER (WHERE parent_id IS NULL AND phase = 'start') as root_name,
      COUNT(*)::int as event_count,
      COUNT(*) FILTER (WHERE error IS NOT NULL)::int as error_count,
      MAX(duration_ms) as duration_ms,
      MIN(created_at) as started_at
    FROM events
    WHERE team_id = ${teamId}
    GROUP BY trace_id
    ORDER BY MIN(created_at) DESC
    LIMIT 100
  `;

  return rows as unknown as TraceRow[];
}

export async function getTraceEvents(
  teamId: string,
  traceId: string,
): Promise<EventRow[]> {
  const rows = await sql`
    SELECT id, trace_id, span_id, parent_id, kind, phase, name, ts,
           duration_ms, data, error, service, created_at
    FROM events
    WHERE team_id = ${teamId} AND trace_id = ${traceId}
    ORDER BY ts ASC
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
    SELECT id, trace_id, span_id, parent_id, kind, phase, name, ts,
           duration_ms, data, error, service, created_at
    FROM events
    WHERE team_id = ${teamId}
      AND (name = 'guard.loop_detected' OR name = 'guard.budget_exceeded' OR error IS NOT NULL)
    ORDER BY created_at DESC
    LIMIT 50
  `;

  return rows as unknown as EventRow[];
}
