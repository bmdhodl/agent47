const DECISION_EVENT_TYPES = new Set([
  "decision.proposed",
  "decision.edited",
  "decision.overridden",
  "decision.approved",
  "decision.bound",
]);

const DECISION_FIELDS = [
  "decision_id",
  "workflow_id",
  "trace_id",
  "object_type",
  "object_id",
  "actor_type",
  "actor_id",
  "event_type",
  "proposal",
  "final",
  "diff",
  "reason",
  "comment",
  "timestamp",
  "binding_state",
  "outcome",
] as const;

export interface TraceEvent {
  kind?: unknown;
  name?: unknown;
  trace_id?: unknown;
  data?: unknown;
}

type DecisionField = (typeof DECISION_FIELDS)[number];
export type DecisionPayload = Record<DecisionField, unknown>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function isDecisionEvent(event: TraceEvent): boolean {
  if (!isRecord(event) || event.kind !== "event") {
    return false;
  }
  if (typeof event.name === "string" && DECISION_EVENT_TYPES.has(event.name)) {
    return isRecord(event.data);
  }
  return isRecord(event.data) && typeof event.data.event_type === "string" && DECISION_EVENT_TYPES.has(event.data.event_type);
}

export function extractDecisionPayload(event: TraceEvent): DecisionPayload | null {
  if (!isDecisionEvent(event)) {
    return null;
  }
  const payload = isRecord(event.data) ? event.data : {};
  const normalized = {} as DecisionPayload;

  for (const field of DECISION_FIELDS) {
    normalized[field] = payload[field];
  }

  normalized.trace_id = normalized.trace_id ?? event.trace_id;
  normalized.event_type = normalized.event_type ?? event.name;
  return normalized;
}

export function extractDecisionEvents(
  events: TraceEvent[],
  filters?: {
    workflowId?: string;
    decisionId?: string;
    traceId?: string;
  },
): DecisionPayload[] {
  return events
    .map((event) => extractDecisionPayload(event))
    .filter((payload): payload is DecisionPayload => payload !== null)
    .filter((payload) => !filters?.workflowId || payload.workflow_id === filters.workflowId)
    .filter((payload) => !filters?.decisionId || payload.decision_id === filters.decisionId)
    .filter((payload) => !filters?.traceId || payload.trace_id === filters.traceId);
}
