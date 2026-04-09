"""Simulate two disposable harnesses sharing one managed-agent session."""
from __future__ import annotations

import json

from agentguard import JsonlFileSink, Tracer

TRACE_PATH = "managed_session_traces.jsonl"
SESSION_ID = "support-session-001"


def _run_harness(service: str, turn_name: str, event_name: str, payload: dict) -> None:
    tracer = Tracer(
        sink=JsonlFileSink(TRACE_PATH),
        service=service,
        session_id=SESSION_ID,
        watermark=False,
    )
    with tracer.trace(turn_name) as span:
        span.event(event_name, data=payload)


def main() -> None:
    _run_harness(
        service="managed-harness-a",
        turn_name="harness.turn",
        event_name="decision.proposed",
        payload={"tool": "search_docs", "query": "agentguard session_id"},
    )
    _run_harness(
        service="managed-harness-b",
        turn_name="harness.turn",
        event_name="tool.result",
        payload={"tool": "search_docs", "status": "ok"},
    )

    with open(TRACE_PATH, encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle if line.strip()]

    matching = [event for event in events if event.get("session_id") == SESSION_ID]
    services = sorted({event["service"] for event in matching})

    print(f"Shared session_id: {SESSION_ID}")
    print(f"Events linked across harnesses: {len(matching)}")
    print("Services:")
    for service in services:
        print(f"  - {service}")
    print(f"Trace file: {TRACE_PATH}")


if __name__ == "__main__":
    main()
