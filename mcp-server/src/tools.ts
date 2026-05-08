import { AgentGuardClient } from "./client.js";
import { extractDecisionEvents } from "./decisions.js";
import type { ToolAnnotations } from "@modelcontextprotocol/sdk/types.js";

export interface ToolDefinition {
  name: string;
  description: string;
  annotations?: ToolAnnotations;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
  handler: (client: AgentGuardClient, args: Record<string, unknown>) => Promise<string>;
}

export const tools: ToolDefinition[] = [
  {
    name: "query_traces",
    description:
      "Read-only search for retained AgentGuard trace summaries from the AgentGuard Read API. " +
      "Requires AGENTGUARD_API_KEY with read access; create keys in the AgentGuard dashboard. " +
      "Returns JSON with a traces array, newest traces first when the API supports ordering; " +
      "items include trace_id, service, root_name, event_count, error_count, duration_ms, " +
      "started_at, API key metadata, and total_cost when available. Defaults to a small page, " +
      "accepts offset pagination, exact service filtering, and ISO 8601 since/until bounds. " +
      "Use this to find candidate trace_id values; use get_trace for the full event tree of one trace " +
      "or get_trace_decisions for decision.* events from a known trace.",
    annotations: {
      title: "Query AgentGuard trace summaries",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum trace summaries to return. Defaults to 20; API maximum is 500.",
        },
        offset: {
          type: "number",
          description: "Zero-based pagination offset for walking additional trace pages.",
        },
        service: {
          type: "string",
          description: "Exact AgentGuard service name to filter by, such as a repo or agent label.",
        },
        since: {
          type: "string",
          description: "ISO 8601 timestamp; include only traces that started at or after this time.",
        },
        until: {
          type: "string",
          description: "ISO 8601 timestamp; include only traces that started at or before this time.",
        },
      },
    },
    handler: async (client, args) => {
      const result = await client.getTraces({
        limit: args.limit ? String(args.limit) : "20",
        offset: args.offset ? String(args.offset) : undefined,
        service: args.service as string | undefined,
        since: args.since as string | undefined,
        until: args.until as string | undefined,
      });
      return JSON.stringify(result, null, 2);
    },
  },
  {
    name: "get_trace",
    description:
      "Get the full event tree for a specific trace by its trace ID. " +
      "Shows all spans, tool calls, LLM calls, guard triggers, and errors.",
    inputSchema: {
      type: "object",
      properties: {
        trace_id: { type: "string", description: "The trace ID to look up" },
      },
      required: ["trace_id"],
    },
    handler: async (client, args) => {
      const result = await client.getTrace(args.trace_id as string);
      return JSON.stringify(result, null, 2);
    },
  },
  {
    name: "get_trace_decisions",
    description:
      "Extract normalized decision.* events from one trace. " +
      "Use this when a workflow includes proposal, override, approval, or binding steps.",
    inputSchema: {
      type: "object",
      properties: {
        trace_id: { type: "string", description: "The trace ID to inspect for decision events" },
      },
      required: ["trace_id"],
    },
    handler: async (client, args) => {
      const traceId = args.trace_id as string;
      const result = await client.getTrace(traceId);
      const events = Array.isArray(result.events) ? result.events : [];
      const decisions = extractDecisionEvents(events as Array<Record<string, unknown>>, {
        traceId,
      });
      return JSON.stringify({ trace_id: traceId, decisions }, null, 2);
    },
  },
  {
    name: "get_alerts",
    description:
      "Get recent guard alerts (loop detection, budget exceeded) and errors. " +
      "Useful for checking if your agents are hitting safety limits.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Max alerts to return (default 50)" },
        since: { type: "string", description: "ISO timestamp — only alerts after this time" },
      },
    },
    handler: async (client, args) => {
      const result = await client.getAlerts({
        limit: args.limit ? String(args.limit) : undefined,
        since: args.since as string | undefined,
      });
      return JSON.stringify(result, null, 2);
    },
  },
  {
    name: "get_usage",
    description:
      "Check your current event quota usage and plan limits. " +
      "Shows event count vs limit, retention period, and plan details.",
    inputSchema: {
      type: "object",
      properties: {},
    },
    handler: async (client) => {
      const result = await client.getUsage();
      const pct = result.event_limit > 0
        ? ((result.event_count / result.event_limit) * 100).toFixed(1)
        : "0";
      return JSON.stringify({ ...result, usage_percent: `${pct}%` }, null, 2);
    },
  },
  {
    name: "get_costs",
    description:
      "Get cost breakdown for the current month: total spend, cost by model, " +
      "and estimated savings from guard interventions.",
    inputSchema: {
      type: "object",
      properties: {},
    },
    handler: async (client) => {
      const result = await client.getCosts();
      return JSON.stringify(result, null, 2);
    },
  },
  {
    name: "check_budget",
    description:
      "Quick pass/fail budget health check. Combines usage quota and cost data " +
      "to give a summary of whether you're within safe operating limits.",
    inputSchema: {
      type: "object",
      properties: {},
    },
    handler: async (client) => {
      const [usage, costs] = await Promise.all([
        client.getUsage(),
        client.getCosts(),
      ]);

      const usagePct = usage.event_limit > 0
        ? (usage.event_count / usage.event_limit) * 100
        : 0;

      const status = usagePct >= 90
        ? "critical"
        : usagePct >= 75
          ? "warning"
          : "healthy";

      return JSON.stringify(
        {
          status,
          plan: usage.plan,
          events: {
            used: usage.event_count,
            limit: usage.event_limit,
            percent: `${usagePct.toFixed(1)}%`,
          },
          costs: {
            monthly_total: costs.monthly.total_cost,
            trace_count: costs.monthly.trace_count,
          },
          savings: costs.savings,
        },
        null,
        2,
      );
    },
  },
];
