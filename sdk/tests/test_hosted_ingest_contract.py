from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest
from conftest import EXPECTED_API_KEY, IngestHandler

from agentguard import Tracer, decision_flow
from agentguard.sinks.http import HttpSink


class TestHostedIngestContract:
    def test_meta_only_batches_fail_like_hosted_ingest(self, ingest_server):
        host, port = ingest_server
        request = urllib.request.Request(
            f"http://{host}:{port}/api/ingest",
            data=b'{"service":"contract-test","kind":"meta","name":"watermark","ts":1}\n',
            headers={
                "Authorization": f"Bearer {EXPECTED_API_KEY}",
                "Content-Type": "application/x-ndjson",
            },
            method="POST",
        )

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(request)

        response = exc_info.value
        assert response.code == 400
        payload = json.loads(response.read().decode())
        assert payload == {
            "error": "No valid events",
            "details": [
                {"line": 0, "error": 'Invalid option: expected one of "span"|"event"'}
            ],
        }

    def test_http_sink_posts_only_hosted_compatible_trace_records(self, ingest_url):
        sink = HttpSink(
            url=ingest_url,
            api_key=EXPECTED_API_KEY,
            batch_size=1,
            flush_interval=60,
            compress=False,
            _allow_private=True,
        )
        tracer = Tracer(sink=sink, service="hosted-contract-test")

        with tracer.trace("agent.run") as ctx:
            trace_id = ctx.trace_id
            ctx.event("tool.result", data={"ok": True})

        sink.shutdown()

        requests = IngestHandler.request_log()
        assert requests, "Expected at least one ingest request"
        assert all(request["status"] == 200 for request in requests)
        assert all(request["rejected"] == 0 for request in requests)

        trace_events = [event for event in IngestHandler.events if event["trace_id"] == trace_id]
        assert len(trace_events) == 3
        assert not any(event["name"] == "watermark" for event in trace_events)
        assert all(event["kind"] in {"span", "event"} for event in trace_events)
        assert all(event["type"] == event["kind"] for event in trace_events)

        base_url = ingest_url.removesuffix("/api/ingest")
        request = urllib.request.Request(f"{base_url}/api/v1/traces?trace_id={trace_id}")
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode())

        assert payload["traces"] == [
            {"trace_id": trace_id, "event_count": len(trace_events), "total_cost": 0.0}
        ]

    def test_decision_trace_events_are_hosted_queryable_by_default(self, ingest_url):
        sink = HttpSink(
            url=ingest_url,
            api_key=EXPECTED_API_KEY,
            batch_size=1,
            flush_interval=60,
            compress=False,
            _allow_private=True,
        )
        tracer = Tracer(sink=sink, service="decision-contract-test")

        with tracer.trace("agent.run") as span:
            trace_id = span.trace_id
            with decision_flow(
                span,
                workflow_id="deploy-approval",
                object_type="deployment",
                object_id="deploy-042",
                actor_type="agent",
                actor_id="release-bot",
            ) as decision:
                decision.proposed({"action": "deploy", "environment": "staging"})
                decision.edited(
                    {"action": "deploy", "environment": "production"},
                    actor_type="human",
                    actor_id="reviewer-123",
                    reason="Customer approved direct rollout",
                )
                decision.approved(actor_type="human", actor_id="reviewer-123")
                decision.bound(
                    actor_type="system",
                    actor_id="deploy-api",
                    binding_state="applied",
                    outcome="success",
                )

        sink.shutdown()

        requests = IngestHandler.request_log()
        assert requests
        assert all(not request["decision_trace_warnings"] for request in requests)

        decision_events = [
            event
            for event in IngestHandler.events
            if event["trace_id"] == trace_id
            and event["name"]
            in {
                "decision.proposed",
                "decision.edited",
                "decision.overridden",
                "decision.approved",
                "decision.bound",
            }
        ]
        assert [event["name"] for event in decision_events] == [
            "decision.proposed",
            "decision.edited",
            "decision.approved",
            "decision.bound",
        ]
        assert [event["data"]["binding_state"] for event in decision_events] == [
            "proposed",
            "edited",
            "approved",
            "applied",
        ]

    def test_local_ingest_reports_decision_trace_warnings_like_dashboard(self, ingest_url):
        invalid_decision_event = {
            "service": "decision-contract-test",
            "kind": "event",
            "type": "event",
            "phase": "emit",
            "trace_id": "trace_invalid_decision",
            "span_id": "span_invalid_decision",
            "parent_id": None,
            "name": "decision.proposed",
            "ts": 1,
            "duration_ms": None,
            "data": {
                "decision_id": "decision_123",
                "workflow_id": "deploy-approval",
                "trace_id": "trace_invalid_decision",
                "object_type": "deployment",
                "object_id": "deploy-042",
                "actor_type": "agent",
                "actor_id": "release-bot",
                "event_type": "decision.proposed",
                "proposal": {"action": "deploy"},
                "final": {"action": "deploy"},
                "diff": "",
                "reason": None,
                "comment": None,
                "timestamp": "2026-04-25T00:00:00Z",
                "binding_state": None,
                "outcome": "proposed",
            },
            "error": None,
            "cost_usd": None,
        }
        request = urllib.request.Request(
            ingest_url,
            data=json.dumps(invalid_decision_event).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {EXPECTED_API_KEY}",
                "Content-Type": "application/x-ndjson",
            },
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode())

        assert payload["accepted"] == 1
        assert payload["rejected"] == 0
        assert payload["decision_trace_warnings"] == [
            {
                "line": 0,
                "error": "Decision payload binding_state must be a non-empty string",
            }
        ]
