import test from "node:test";
import assert from "node:assert/strict";

import { tools } from "../tools.js";

test("query_traces exposes read-only annotations and agent-use guidance", () => {
  const tool = tools.find((entry) => entry.name === "query_traces");
  assert.ok(tool);

  assert.equal(tool.annotations?.readOnlyHint, true);
  assert.equal(tool.annotations?.destructiveHint, false);
  assert.equal(tool.annotations?.idempotentHint, true);
  assert.match(tool.description, /AgentGuard Read API/);
  assert.match(tool.description, /Read-only search/);
  assert.match(tool.description, /get_trace/);
});

test("get_trace_decisions returns normalized decision payloads", async () => {
  const tool = tools.find((entry) => entry.name === "get_trace_decisions");
  assert.ok(tool);

  const fakeClient = {
    async getTrace(traceId: string) {
      return {
        trace_id: traceId,
        events: [
          {
            kind: "event",
            name: "decision.proposed",
            trace_id: traceId,
            data: {
              decision_id: "dec_1",
              workflow_id: "wf_1",
              trace_id: traceId,
              object_type: "deployment",
              object_id: "deploy_1",
              actor_type: "agent",
              actor_id: "planner",
              event_type: "decision.proposed",
              proposal: { action: "deploy" },
              final: { action: "deploy" },
              diff: "",
              reason: null,
              comment: null,
              timestamp: "2026-04-07T00:00:00Z",
              binding_state: null,
              outcome: "proposed",
            },
          },
          {
            kind: "event",
            name: "tool.result",
            trace_id: traceId,
            data: { tool_name: "search" },
          },
        ],
      };
    },
  };

  const output = await tool!.handler(fakeClient as never, { trace_id: "trace_1" });
  const parsed = JSON.parse(output) as { trace_id: string; decisions: Array<{ event_type: string }> };

  assert.equal(parsed.trace_id, "trace_1");
  assert.equal(parsed.decisions.length, 1);
  assert.equal(parsed.decisions[0].event_type, "decision.proposed");
});

test("check_budget returns warning status and cost summary", async () => {
  const tool = tools.find((entry) => entry.name === "check_budget");
  assert.ok(tool);

  const fakeClient = {
    async getUsage() {
      return {
        plan: "team",
        current_month: "2026-05",
        event_count: 80,
        event_limit: 100,
        retention_days: 30,
        max_keys: 5,
        max_users: 10,
      };
    },
    async getCosts() {
      return {
        monthly: { total_cost: 12.34, trace_count: 8 },
        by_model: [],
        savings: { guard_events: 2, estimated_savings: 4.56 },
      };
    },
  };

  const output = await tool!.handler(fakeClient as never, {});
  const parsed = JSON.parse(output) as {
    status: string;
    events: { percent: string };
    costs: { monthly_total: number; trace_count: number };
    savings: { guard_events: number; estimated_savings: number };
  };

  assert.equal(parsed.status, "warning");
  assert.equal(parsed.events.percent, "80.0%");
  assert.equal(parsed.costs.monthly_total, 12.34);
  assert.equal(parsed.costs.trace_count, 8);
  assert.equal(parsed.savings.guard_events, 2);
});

test("all tools expose object input schemas", () => {
  for (const tool of tools) {
    assert.equal(tool.inputSchema.type, "object", tool.name);
    assert.ok(tool.inputSchema.properties, tool.name);
  }
});
