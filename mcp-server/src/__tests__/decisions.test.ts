import test from "node:test";
import assert from "node:assert/strict";

import { extractDecisionEvents, extractDecisionPayload, isDecisionEvent } from "../decisions.js";

test("isDecisionEvent recognizes decision lifecycle events", () => {
  const event = {
    kind: "event",
    name: "decision.approved",
    trace_id: "trace_1",
    data: {
      decision_id: "dec_1",
      workflow_id: "wf_1",
      event_type: "decision.approved",
    },
  };

  assert.equal(isDecisionEvent(event), true);
  assert.equal(isDecisionEvent({ kind: "event", name: "tool.result", data: {} }), false);
});

test("extractDecisionPayload normalizes trace and event fields", () => {
  const payload = extractDecisionPayload({
    kind: "event",
    name: "decision.bound",
    trace_id: "trace_1",
    data: {
      decision_id: "dec_1",
      workflow_id: "wf_1",
      object_type: "deployment",
      object_id: "deploy_1",
      actor_type: "system",
      actor_id: "deploy-api",
      proposal: { action: "deploy" },
      final: { action: "deploy" },
      diff: "",
      reason: null,
      comment: null,
      timestamp: "2026-04-07T00:00:00Z",
      binding_state: "applied",
      outcome: "success",
    },
  });

  assert.equal(payload?.trace_id, "trace_1");
  assert.equal(payload?.event_type, "decision.bound");
  assert.equal(payload?.binding_state, "applied");
});

test("extractDecisionEvents filters by workflow and trace", () => {
  const decisions = extractDecisionEvents(
    [
      {
        kind: "event",
        name: "decision.proposed",
        trace_id: "trace_a",
        data: {
          decision_id: "dec_a",
          workflow_id: "wf_a",
          trace_id: "trace_a",
          object_type: "deployment",
          object_id: "deploy_a",
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
        name: "decision.approved",
        trace_id: "trace_b",
        data: {
          decision_id: "dec_b",
          workflow_id: "wf_b",
          trace_id: "trace_b",
          object_type: "ticket",
          object_id: "ticket_b",
          actor_type: "human",
          actor_id: "reviewer",
          event_type: "decision.approved",
          proposal: { action: "close" },
          final: { action: "close" },
          diff: "",
          reason: null,
          comment: null,
          timestamp: "2026-04-07T00:01:00Z",
          binding_state: null,
          outcome: "approved",
        },
      },
    ],
    { workflowId: "wf_b", traceId: "trace_b" },
  );

  assert.equal(decisions.length, 1);
  assert.equal(decisions[0].decision_id, "dec_b");
});
