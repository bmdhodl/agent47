import pytest

from agentguard import (
    Tracer,
    decision_flow,
    extract_decision_events,
    extract_decision_payload,
    is_decision_event,
    log_decision_bound,
    log_decision_edited,
    log_decision_proposed,
)


def _capture_events(tracer, fn):
    captured = []

    class CaptureSink:
        def emit(self, event):
            captured.append(event)

    tracer._sink = CaptureSink()
    fn()
    return captured


def test_log_decision_proposed_emits_required_schema_fields():
    tracer = Tracer(watermark=False)

    def run():
        with tracer.trace("agent.run") as span:
            payload = log_decision_proposed(
                span,
                workflow_id="wf_123",
                object_type="deployment",
                object_id="deploy_456",
                actor_type="agent",
                actor_id="planner",
                proposal={"action": "deploy", "target": "staging"},
                reason="Checks passed",
                comment="Awaiting approval",
            )
            assert payload["event_type"] == "decision.proposed"
            assert payload["trace_id"] == span.trace_id

    events = _capture_events(tracer, run)
    decision_events = [event for event in events if event["name"] == "decision.proposed"]
    assert len(decision_events) == 1

    payload = decision_events[0]["data"]
    required = {
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
    }
    assert required.issubset(payload)
    assert payload["final"] == payload["proposal"]
    assert payload["outcome"] == "proposed"


def test_log_decision_edited_computes_diff_from_original_proposal():
    tracer = Tracer(watermark=False)
    proposal = {"action": "deploy", "target": "staging"}
    final = {"action": "deploy", "target": "production"}

    def run():
        with tracer.trace("agent.run") as span:
            payload = log_decision_edited(
                span,
                decision_id="dec_1",
                workflow_id="wf_1",
                object_type="deployment",
                object_id="deploy_1",
                actor_type="human",
                actor_id="alice",
                proposal=proposal,
                final=final,
                reason="Customer requested production push",
                comment="Changing target before approval",
            )
            assert payload["proposal"] == proposal
            assert payload["final"] == final

    events = _capture_events(tracer, run)
    payload = next(event["data"] for event in events if event["name"] == "decision.edited")
    assert payload["diff"].startswith("--- proposal\n+++ final\n")
    assert '-  "target": "staging"' in payload["diff"]
    assert '+  "target": "production"' in payload["diff"]


def test_decision_flow_keeps_decision_state_across_events():
    tracer = Tracer(watermark=False)

    def run():
        with tracer.trace("agent.run") as span, decision_flow(
            span,
            workflow_id="wf_2",
            object_type="pull_request",
            object_id="pr_42",
            actor_type="agent",
            actor_id="review-bot",
            span_name="approval.flow",
        ) as decision:
            decision.proposed(
                {"action": "merge", "branch": "main"},
                reason="All checks green",
            )
            decision.overridden(
                {"action": "merge", "branch": "release"},
                actor_type="human",
                actor_id="pat",
                reason="Ship to release branch first",
                comment="Manual route change",
            )
            decision.approved(
                actor_type="human",
                actor_id="pat",
                comment="Approved after override",
            )
            decision.bound(
                actor_type="system",
                actor_id="github",
                binding_state="merged",
                outcome="success",
                comment="Merge API accepted",
            )

    events = _capture_events(tracer, run)
    payloads = [event["data"] for event in events if event.get("name", "").startswith("decision.")]
    assert [payload["event_type"] for payload in payloads] == [
        "decision.proposed",
        "decision.overridden",
        "decision.approved",
        "decision.bound",
    ]
    decision_ids = {payload["decision_id"] for payload in payloads}
    assert len(decision_ids) == 1
    assert payloads[1]["proposal"] == {"action": "merge", "branch": "main"}
    assert payloads[1]["final"] == {"action": "merge", "branch": "release"}
    assert payloads[2]["final"] == {"action": "merge", "branch": "release"}
    assert payloads[3]["binding_state"] == "merged"
    assert payloads[3]["outcome"] == "success"


def test_decision_flow_accepts_tracer_for_top_level_workflow():
    tracer = Tracer(watermark=False)

    def run():
        with decision_flow(
            tracer,
            workflow_id="wf_top",
            object_type="ticket",
            object_id="ticket_9",
            actor_type="agent",
            actor_id="planner",
        ) as decision:
            payload = decision.proposed({"action": "close_ticket"})
            assert payload["trace_id"] == decision.trace_id

    events = _capture_events(tracer, run)
    span_names = [event["name"] for event in events if event["kind"] == "span"]
    assert "decision.flow" in span_names
    decision_events = [event for event in events if event["name"] == "decision.proposed"]
    assert len(decision_events) == 1


def test_decision_flow_requires_proposal_before_approval():
    tracer = Tracer(watermark=False)

    def run():
        with decision_flow(
            tracer,
            workflow_id="wf_missing",
            object_type="ticket",
            object_id="ticket_10",
            actor_type="agent",
            actor_id="planner",
        ) as decision, pytest.raises(ValueError, match="proposal is required"):
            decision.approved(actor_type="human", actor_id="reviewer")

    _capture_events(tracer, run)


def test_log_decision_bound_requires_explicit_binding_outcome_fields():
    tracer = Tracer(watermark=False)

    def run():
        with tracer.trace("agent.run") as span, pytest.raises(
            ValueError,
            match="binding_state must be a non-empty string",
        ):
            log_decision_bound(
                span,
                decision_id="dec_2",
                workflow_id="wf_3",
                object_type="deployment",
                object_id="deploy_2",
                actor_type="system",
                actor_id="orchestrator",
                proposal={"action": "deploy"},
                binding_state="",
                outcome="success",
            )

    _capture_events(tracer, run)


def test_log_decision_proposed_rejects_none_proposal():
    tracer = Tracer(watermark=False)

    def run():
        with tracer.trace("agent.run") as span, pytest.raises(
            ValueError,
            match="proposal must not be None",
        ):
            log_decision_proposed(
                span,
                workflow_id="wf_none",
                object_type="deployment",
                object_id="deploy_none",
                actor_type="agent",
                actor_id="planner",
                proposal=None,
            )

    _capture_events(tracer, run)


def test_decision_flow_rejects_reserved_span_data_keys():
    tracer = Tracer(watermark=False)

    def run():
        with pytest.raises(
            ValueError,
            match="span_data cannot override reserved decision-flow keys: workflow_id",
        ), decision_flow(
            tracer,
            workflow_id="wf_reserved",
            object_type="ticket",
            object_id="ticket_11",
            actor_type="agent",
            actor_id="planner",
            span_data={"workflow_id": "bad_override"},
        ):
            pass

    _capture_events(tracer, run)


def test_decision_payload_preserves_schema_for_large_non_serializable_values():
    tracer = Tracer(watermark=False)
    large_object = {"items": ["x" * 30000, object(), "y" * 30000]}

    def run():
        with tracer.trace("agent.run") as span:
            log_decision_edited(
                span,
                decision_id="dec_big",
                workflow_id="wf_big",
                object_type="deployment",
                object_id="deploy_big",
                actor_type="human",
                actor_id="reviewer",
                proposal=large_object,
                final={"items": ["done"]},
                diff="z" * 20000,
                reason="r" * 4000,
                comment="c" * 4000,
            )

    events = _capture_events(tracer, run)
    payload = next(event["data"] for event in events if event["name"] == "decision.edited")
    required = {
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
    }
    assert required.issubset(payload)
    assert payload["proposal"]["_truncated"] is True
    assert payload["final"] == {"items": ["done"]}
    assert isinstance(payload["diff"], str)
    assert payload["diff"].endswith("...[truncated]")


def test_extract_decision_payload_normalizes_trace_fields():
    raw_event = {
        "kind": "event",
        "name": "decision.approved",
        "trace_id": "trace_123",
        "data": {
            "decision_id": "dec_1",
            "workflow_id": "wf_1",
            "object_type": "deployment",
            "object_id": "deploy_1",
            "actor_type": "human",
            "actor_id": "reviewer",
            "proposal": {"action": "deploy"},
            "final": {"action": "deploy"},
            "diff": "",
            "reason": "looks good",
            "comment": None,
            "timestamp": "2026-04-07T00:00:00Z",
            "binding_state": None,
            "outcome": "approved",
        },
    }

    assert is_decision_event(raw_event) is True
    payload = extract_decision_payload(raw_event)
    assert payload["event_type"] == "decision.approved"
    assert payload["trace_id"] == "trace_123"


def test_extract_decision_events_filters_by_workflow():
    events = [
        {
            "kind": "event",
            "name": "decision.proposed",
            "trace_id": "trace_a",
            "data": {
                "decision_id": "dec_a",
                "workflow_id": "wf_a",
                "trace_id": "trace_a",
                "object_type": "deployment",
                "object_id": "deploy_a",
                "actor_type": "agent",
                "actor_id": "planner",
                "event_type": "decision.proposed",
                "proposal": {"action": "deploy"},
                "final": {"action": "deploy"},
                "diff": "",
                "reason": None,
                "comment": None,
                "timestamp": "2026-04-07T00:00:00Z",
                "binding_state": None,
                "outcome": "proposed",
            },
        },
        {
            "kind": "event",
            "name": "decision.approved",
            "trace_id": "trace_b",
            "data": {
                "decision_id": "dec_b",
                "workflow_id": "wf_b",
                "trace_id": "trace_b",
                "object_type": "ticket",
                "object_id": "ticket_b",
                "actor_type": "human",
                "actor_id": "reviewer",
                "event_type": "decision.approved",
                "proposal": {"action": "close"},
                "final": {"action": "close"},
                "diff": "",
                "reason": None,
                "comment": None,
                "timestamp": "2026-04-07T00:01:00Z",
                "binding_state": None,
                "outcome": "approved",
            },
        },
    ]

    payloads = extract_decision_events(events, workflow_id="wf_b")
    assert len(payloads) == 1
    assert payloads[0]["decision_id"] == "dec_b"


def test_is_decision_event_ignores_non_string_names_and_event_types():
    assert is_decision_event(
        {
            "kind": "event",
            "name": ["decision.proposed"],
            "data": {},
        }
    ) is False
    assert is_decision_event(
        {
            "kind": "event",
            "name": "custom.event",
            "data": {"event_type": ["decision.proposed"]},
        }
    ) is False
