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
  total_cost: number | null;
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

export interface TraceListOpts {
  limit?: number;
  offset?: number;
  service?: string;
  since?: string;
  until?: string;
}

export async function getTraceList(
  teamId: string,
  opts?: TraceListOpts,
): Promise<TraceRow[]> {
  const limit = Math.min(opts?.limit ?? 100, 500);
  const offset = opts?.offset ?? 0;

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
      MIN(ak.prefix) as api_key_prefix,
      SUM(e.cost_usd) as total_cost
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId}
      ${opts?.service ? sql`AND e.service = ${opts.service}` : sql``}
      ${opts?.since ? sql`AND e.created_at >= ${opts.since}::timestamptz` : sql``}
      ${opts?.until ? sql`AND e.created_at <= ${opts.until}::timestamptz` : sql``}
    GROUP BY e.trace_id
    ORDER BY MIN(e.created_at) DESC
    LIMIT ${limit} OFFSET ${offset}
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

export interface AlertsOpts {
  limit?: number;
  since?: string;
}

export async function getAlerts(
  teamId: string,
  opts?: AlertsOpts,
): Promise<EventRow[]> {
  const limit = Math.min(opts?.limit ?? 50, 200);

  const rows = await sql`
    SELECT e.id, e.trace_id, e.span_id, e.parent_id, e.kind, e.phase, e.name, e.ts,
           e.duration_ms, e.data, e.error, e.service, e.created_at,
           ak.name as api_key_name, ak.prefix as api_key_prefix
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId}
      AND (e.name = 'guard.loop_detected' OR e.name = 'guard.budget_exceeded' OR e.error IS NOT NULL)
      ${opts?.since ? sql`AND e.created_at >= ${opts.since}::timestamptz` : sql``}
    ORDER BY e.created_at DESC
    LIMIT ${limit}
  `;

  return rows as unknown as EventRow[];
}

export interface SavingsStats {
  guard_events: number;
  estimated_savings: number;
}

export async function getSavingsStats(teamId: string): Promise<SavingsStats> {
  const rows = await sql`
    SELECT
      COUNT(*)::int as guard_events,
      COALESCE(SUM(
        CASE WHEN e.cost_usd IS NOT NULL THEN e.cost_usd ELSE 0.50 END
      ), 0) as estimated_savings
    FROM events e
    WHERE e.team_id = ${teamId}
      AND e.name IN ('guard.loop_detected', 'guard.budget_exceeded')
      AND e.created_at >= date_trunc('month', now())
  `;

  return {
    guard_events: rows.length > 0 ? Number(rows[0].guard_events) : 0,
    estimated_savings: rows.length > 0 ? Number(rows[0].estimated_savings) : 0,
  };
}

export interface MonthlyCost {
  total_cost: number;
  trace_count: number;
}

export async function getMonthlyCost(teamId: string): Promise<MonthlyCost> {
  const rows = await sql`
    SELECT
      COALESCE(SUM(e.cost_usd), 0) as total_cost,
      COUNT(DISTINCT e.trace_id)::int as trace_count
    FROM events e
    WHERE e.team_id = ${teamId}
      AND e.created_at >= date_trunc('month', now())
  `;

  return {
    total_cost: rows.length > 0 ? Number(rows[0].total_cost) : 0,
    trace_count: rows.length > 0 ? Number(rows[0].trace_count) : 0,
  };
}

export interface CostByModel {
  model: string;
  total_cost: number;
  call_count: number;
}

export async function getCostByModel(teamId: string): Promise<CostByModel[]> {
  const rows = await sql`
    SELECT
      COALESCE(e.data->>'model', 'unknown') as model,
      SUM(e.cost_usd) as total_cost,
      COUNT(*)::int as call_count
    FROM events e
    WHERE e.team_id = ${teamId}
      AND e.cost_usd IS NOT NULL
      AND e.created_at >= date_trunc('month', now())
    GROUP BY e.data->>'model'
    ORDER BY SUM(e.cost_usd) DESC
    LIMIT 20
  `;

  return rows as unknown as CostByModel[];
}

export interface CostByKey {
  api_key_name: string;
  api_key_prefix: string;
  total_cost: number;
  trace_count: number;
}

export async function getCostByKey(teamId: string): Promise<CostByKey[]> {
  const rows = await sql`
    SELECT
      COALESCE(ak.name, 'Unknown') as api_key_name,
      COALESCE(ak.prefix, '—') as api_key_prefix,
      SUM(e.cost_usd) as total_cost,
      COUNT(DISTINCT e.trace_id)::int as trace_count
    FROM events e
    LEFT JOIN api_keys ak ON ak.id = e.api_key_id
    WHERE e.team_id = ${teamId}
      AND e.cost_usd IS NOT NULL
      AND e.created_at >= date_trunc('month', now())
    GROUP BY ak.name, ak.prefix
    ORDER BY SUM(e.cost_usd) DESC
    LIMIT 10
  `;

  return rows as unknown as CostByKey[];
}

export interface ExpensiveTrace {
  trace_id: string;
  root_name: string;
  total_cost: number;
  event_count: number;
  started_at: string;
}

export async function getExpensiveTraces(teamId: string): Promise<ExpensiveTrace[]> {
  const rows = await sql`
    SELECT
      e.trace_id,
      MIN(e.name) FILTER (WHERE e.parent_id IS NULL AND e.phase = 'start') as root_name,
      SUM(e.cost_usd) as total_cost,
      COUNT(*)::int as event_count,
      MIN(e.created_at) as started_at
    FROM events e
    WHERE e.team_id = ${teamId}
      AND e.created_at >= date_trunc('month', now())
    GROUP BY e.trace_id
    HAVING SUM(e.cost_usd) > 0
    ORDER BY SUM(e.cost_usd) DESC
    LIMIT 10
  `;

  return rows as unknown as ExpensiveTrace[];
}
