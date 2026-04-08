import test from "node:test";
import assert from "node:assert/strict";

import { tools } from "../tools.js";

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
