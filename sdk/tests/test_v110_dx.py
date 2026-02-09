"""Tests for v1.1.0 DX improvements: Tracer context manager, summarize_trace."""
import json
import os
import tempfile
import unittest

from agentguard.tracing import Tracer
from agentguard.evaluation import summarize_trace


class TestTracerContextManager(unittest.TestCase):
    """Test Tracer as a context manager for clean shutdown."""

    def test_context_manager_returns_tracer(self):
        tracer = Tracer()
        with tracer as t:
            self.assertIs(t, tracer)

    def test_context_manager_calls_shutdown(self):
        shutdown_called = False

        class MockSink:
            def emit(self, event):
                pass

            def shutdown(self):
                nonlocal shutdown_called
                shutdown_called = True

        sink = MockSink()
        with Tracer(sink=sink) as tracer:
            with tracer.trace("test"):
                pass

        self.assertTrue(shutdown_called)

    def test_context_manager_no_shutdown_if_missing(self):
        """Sinks without shutdown() should not crash."""
        class MinimalSink:
            def emit(self, event):
                pass

        sink = MinimalSink()
        with Tracer(sink=sink) as tracer:
            with tracer.trace("test"):
                pass
        # No error

    def test_context_manager_shutdown_on_exception(self):
        shutdown_called = False

        class MockSink:
            def emit(self, event):
                pass

            def shutdown(self):
                nonlocal shutdown_called
                shutdown_called = True

        with self.assertRaises(ValueError):
            with Tracer(sink=MockSink()) as tracer:
                raise ValueError("test error")

        self.assertTrue(shutdown_called)

    def test_context_manager_does_not_suppress_exceptions(self):
        with self.assertRaises(RuntimeError):
            with Tracer() as tracer:
                raise RuntimeError("should propagate")


class TestSummarizeTrace(unittest.TestCase):
    """Test summarize_trace() API."""

    def _make_trace_file(self, events):
        """Write events to a temp JSONL file and return the path."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        )
        for event in events:
            f.write(json.dumps(event) + "\n")
        f.close()
        return f.name

    def test_summarize_from_file(self):
        events = [
            {"kind": "span", "phase": "start", "name": "agent.run", "ts": 1.0},
            {"kind": "event", "phase": "emit", "name": "tool.search", "ts": 1.1},
            {"kind": "span", "phase": "end", "name": "agent.run", "ts": 1.5, "duration_ms": 500},
        ]
        path = self._make_trace_file(events)
        try:
            result = summarize_trace(path)
            self.assertEqual(result["total_events"], 3)
            self.assertEqual(result["spans"], 2)  # start + end
            self.assertEqual(result["events"], 1)
            self.assertAlmostEqual(result["duration_ms"], 500.0)
        finally:
            os.unlink(path)

    def test_summarize_from_list(self):
        events = [
            {"kind": "span", "phase": "start", "name": "tool.search", "ts": 1.0},
            {"kind": "span", "phase": "end", "name": "tool.search", "ts": 1.2, "duration_ms": 200},
            {"kind": "event", "phase": "emit", "name": "llm.result", "ts": 1.3},
        ]
        result = summarize_trace(events)
        self.assertEqual(result["total_events"], 3)
        self.assertEqual(result["tool_calls"], 1)
        self.assertAlmostEqual(result["duration_ms"], 200.0)

    def test_summarize_cost_from_top_level(self):
        events = [
            {"kind": "span", "phase": "end", "name": "llm", "cost_usd": 0.05},
            {"kind": "span", "phase": "end", "name": "llm2", "cost_usd": 0.03},
        ]
        result = summarize_trace(events)
        self.assertAlmostEqual(result["cost_usd"], 0.08, places=4)

    def test_summarize_cost_from_data_dict(self):
        events = [
            {"kind": "event", "phase": "emit", "name": "llm.result",
             "data": {"cost_usd": 0.02}},
        ]
        result = summarize_trace(events)
        self.assertAlmostEqual(result["cost_usd"], 0.02, places=4)

    def test_summarize_errors(self):
        events = [
            {"kind": "span", "phase": "end", "name": "agent", "error": {"type": "RuntimeError", "message": "fail"}},
            {"kind": "event", "phase": "emit", "name": "step"},
        ]
        result = summarize_trace(events)
        self.assertEqual(result["errors"], 1)

    def test_summarize_loop_detections(self):
        events = [
            {"kind": "event", "phase": "emit", "name": "guard.loop_detected"},
            {"kind": "event", "phase": "emit", "name": "guard.loop_detected"},
        ]
        result = summarize_trace(events)
        self.assertEqual(result["loop_detections"], 2)

    def test_summarize_empty_list(self):
        result = summarize_trace([])
        self.assertEqual(result["total_events"], 0)
        self.assertEqual(result["cost_usd"], 0.0)

    def test_summarize_empty_file(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.close()
        try:
            result = summarize_trace(f.name)
            self.assertEqual(result["total_events"], 0)
        finally:
            os.unlink(f.name)

    def test_summarize_invalid_input_type(self):
        with self.assertRaises(TypeError):
            summarize_trace(42)

    def test_summarize_real_trace(self):
        """End-to-end: trace some events, then summarize."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            from agentguard.tracing import JsonlFileSink
            sink = JsonlFileSink(path)
            tracer = Tracer(sink=sink, service="test")
            with tracer.trace("agent.run") as ctx:
                ctx.event("tool.search", data={"q": "test"})
                with ctx.span("tool.lookup"):
                    ctx.event("tool.result", data={"found": True})

            result = summarize_trace(path)
            self.assertGreater(result["total_events"], 0)
            self.assertGreater(result["spans"], 0)
            self.assertGreater(result["events"], 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
