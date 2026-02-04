import json
import tempfile

from agentguard.tracing import JsonlFileSink, Tracer


def test_trace_emits_events():
    with tempfile.NamedTemporaryFile() as tmp:
        tracer = Tracer(sink=JsonlFileSink(tmp.name))
        with tracer.trace("agent.run", data={"user": "u1"}) as span:
            span.event("reasoning.step", data={"step": 1})
        tmp.seek(0)
        lines = [line for line in tmp.read().decode("utf-8").splitlines() if line]

    events = [json.loads(line) for line in lines]
    assert len(events) >= 2
    names = [e["name"] for e in events]
    assert "agent.run" in names
    assert "reasoning.step" in names
