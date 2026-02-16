import json
import tempfile
import unittest

from agentguard.tracing import JsonlFileSink, Tracer, TraceContext


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


class TestTraceContextCost(unittest.TestCase):
    def test_cost_property_lazy_init(self) -> None:
        """Accessing .cost returns a CostTracker."""
        from agentguard.cost import CostTracker

        tracer = Tracer()
        ctx = TraceContext(
            tracer=tracer, trace_id="t1", span_id="s1",
            parent_id=None, name="test", data=None,
        )
        tracker = ctx.cost
        self.assertIsInstance(tracker, CostTracker)

    def test_cost_property_same_instance(self) -> None:
        """Repeated access returns the same CostTracker."""
        tracer = Tracer()
        ctx = TraceContext(
            tracer=tracer, trace_id="t1", span_id="s1",
            parent_id=None, name="test", data=None,
        )
        self.assertIs(ctx.cost, ctx.cost)

    def test_cost_accumulates_within_trace(self) -> None:
        """CostTracker on a context accumulates costs."""
        tracer = Tracer()
        ctx = TraceContext(
            tracer=tracer, trace_id="t1", span_id="s1",
            parent_id=None, name="test", data=None,
        )
        ctx.cost.add("gpt-4o", input_tokens=1000, output_tokens=500, provider="openai")
        self.assertGreater(ctx.cost.total, 0)


class TestEmitCostUsd(unittest.TestCase):
    def test_cost_usd_included_when_set(self) -> None:
        """_emit with cost_usd includes it in the event dict."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), watermark=False)
        tracer._emit(
            kind="event", phase="emit", trace_id="t1", span_id="s1",
            parent_id=None, name="llm.result", cost_usd=0.005,
        )
        self.assertEqual(len(captured), 1)
        self.assertIn("cost_usd", captured[0])
        self.assertAlmostEqual(captured[0]["cost_usd"], 0.005)

    def test_cost_usd_omitted_when_none(self) -> None:
        """_emit without cost_usd does not include the key."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), watermark=False)
        tracer._emit(
            kind="event", phase="emit", trace_id="t1", span_id="s1",
            parent_id=None, name="llm.result",
        )
        self.assertEqual(len(captured), 1)
        self.assertNotIn("cost_usd", captured[0])

    def test_cost_usd_zero_is_included(self) -> None:
        """_emit with cost_usd=0.0 includes it (zero is valid)."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), watermark=False)
        tracer._emit(
            kind="event", phase="emit", trace_id="t1", span_id="s1",
            parent_id=None, name="llm.result", cost_usd=0.0,
        )
        self.assertEqual(len(captured), 1)
        self.assertIn("cost_usd", captured[0])
        self.assertEqual(captured[0]["cost_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()
