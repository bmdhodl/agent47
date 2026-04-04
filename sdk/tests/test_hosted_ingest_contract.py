from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import pytest
from conftest import EXPECTED_API_KEY, IngestHandler

from agentguard import Tracer
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
        time.sleep(0.2)

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
