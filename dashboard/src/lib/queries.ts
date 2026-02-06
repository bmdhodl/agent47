import { createClient } from "@/lib/supabase/server";

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
  const supabase = createClient();

  // Use the trace_summary view
  const { data, error } = await supabase
    .from("trace_summary")
    .select("*")
    .eq("team_id", teamId)
    .order("started_at", { ascending: false })
    .limit(100);

  if (error) {
    console.error("getTraceList error:", error);
    return [];
  }

  return (data ?? []) as TraceRow[];
}

export async function getTraceEvents(
  teamId: string,
  traceId: string,
): Promise<EventRow[]> {
  const supabase = createClient();

  const { data, error } = await supabase
    .from("events")
    .select("*")
    .eq("team_id", teamId)
    .eq("trace_id", traceId)
    .order("ts", { ascending: true });

  if (error) {
    console.error("getTraceEvents error:", error);
    return [];
  }

  return (data ?? []) as EventRow[];
}

export async function getUsageStats(teamId: string) {
  const supabase = createClient();
  const month = new Date().toISOString().slice(0, 7);

  const { data } = await supabase
    .from("usage")
    .select("event_count")
    .eq("team_id", teamId)
    .eq("month", month)
    .single();

  return { currentMonth: month, eventCount: data?.event_count ?? 0 };
}

export async function getAlerts(teamId: string): Promise<EventRow[]> {
  const supabase = createClient();

  const { data, error } = await supabase
    .from("events")
    .select("*")
    .eq("team_id", teamId)
    .or(
      "name.eq.guard.loop_detected,name.eq.guard.budget_exceeded,error.not.is.null",
    )
    .order("created_at", { ascending: false })
    .limit(50);

  if (error) {
    console.error("getAlerts error:", error);
    return [];
  }

  return (data ?? []) as EventRow[];
}
