"""Tests for Developer Experience features: repr, docstrings, guards param, summarize_trace."""
import json
import os
import tempfile
import unittest

from agentguard import (
    Tracer,
    LoopGuard,
    BudgetGuard,
    TimeoutGuard,
    JsonlFileSink,
    StdoutSink,
    HttpSink,
    EvalSuite,
    LoopDetected,
)
from agentguard.tracing import TraceContext
from agentguard.evaluation import summarize_trace


# ---------------------------------------------------------------------------
# Repr tests
# ---------------------------------------------------------------------------


class TestGuardRepr(unittest.TestCase):
    def test_loop_guard_repr(self):
        guard = LoopGuard(max_repeats=3, window=5)
        self.assertEqual(repr(guard), "LoopGuard(max_repeats=3, window=5)")

    def test_budget_guard_repr_all_limits(self):
        guard = BudgetGuard(max_tokens=100, max_calls=10, max_cost_usd=5.0)
        r = repr(guard)
        self.assertIn("max_tokens=100", r)
        self.assertIn("max_calls=10", r)
        self.assertIn("max_cost_usd=5.0", r)

    def test_budget_guard_repr_cost_only(self):
        guard = BudgetGuard(max_cost_usd=2.50)
        self.assertEqual(repr(guard), "BudgetGuard(max_cost_usd=2.5)")

    def test_timeout_guard_repr(self):
        guard = TimeoutGuard(max_seconds=30)
        self.assertEqual(repr(guard), "TimeoutGuard(max_seconds=30)")


class TestSinkRepr(unittest.TestCase):
    def test_stdout_sink_repr(self):
        sink = StdoutSink()
        self.assertEqual(repr(sink), "StdoutSink()")

    def test_jsonl_file_sink_repr(self):
        sink = JsonlFileSink("traces.jsonl")
        self.assertEqual(repr(sink), "JsonlFileSink('traces.jsonl')")


class TestTracerRepr(unittest.TestCase):
    def test_tracer_repr_default(self):
        tracer = Tracer()
        self.assertEqual(repr(tracer), "Tracer(service='app', sink=StdoutSink())")

    def test_tracer_repr_custom(self):
        sink = JsonlFileSink("test.jsonl")
        tracer = Tracer(sink=sink, service="my-agent")
        self.assertEqual(
            repr(tracer),
            "Tracer(service='my-agent', sink=JsonlFileSink('test.jsonl'))",
        )


# ---------------------------------------------------------------------------
# Docstrings
# ---------------------------------------------------------------------------


class TestDocstrings(unittest.TestCase):
    def test_tracer_has_docstring(self):
        self.assertIn("Tracer", Tracer.__doc__)

    def test_loop_guard_has_usage_example(self):
        self.assertIn("LoopGuard(", LoopGuard.__doc__)

    def test_budget_guard_has_usage_example(self):
        self.assertIn("BudgetGuard(", BudgetGuard.__doc__)

    def test_timeout_guard_has_usage_example(self):
        self.assertIn("TimeoutGuard(", TimeoutGuard.__doc__)

    def test_jsonl_file_sink_has_docstring(self):
        self.assertIn("JSONL", JsonlFileSink.__doc__)

    def test_eval_suite_has_docstring(self):
        self.assertIn("assertion", EvalSuite.__doc__)

    def test_check_method_has_docstring(self):
        self.assertIsNotNone(LoopGuard.check.__doc__)

    def test_consume_method_has_docstring(self):
        self.assertIsNotNone(BudgetGuard.consume.__doc__)


# ---------------------------------------------------------------------------
# Tracer guards param
# ---------------------------------------------------------------------------


class TestTracerGuardsParam(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_tracer_with_loop_guard_auto_checks(self):
        loop_guard = LoopGuard(max_repeats=3)
        tracer = Tracer(
            sink=JsonlFileSink(self.path),
            service="test",
            guards=[loop_guard],
        )
        with tracer.trace("agent.run") as span:
            span.event("tool.search", data={"query": "a"})
            span.event("tool.search", data={"query": "a"})
            with self.assertRaises(LoopDetected):
                span.event("tool.search", data={"query": "a"})

    def test_tracer_without_guards_no_error(self):
        tracer = Tracer(sink=JsonlFileSink(self.path), service="test")
        with tracer.trace("agent.run") as span:
            for _ in range(10):
                span.event("tool.search", data={"query": "a"})

    def test_tracer_guards_default_empty(self):
        tracer = Tracer()
        self.assertEqual(tracer._guards, [])


# ---------------------------------------------------------------------------
# Error messages
# ---------------------------------------------------------------------------


class TestBetterErrorMessages(unittest.TestCase):
    def test_loop_detected_includes_args(self):
        guard = LoopGuard(max_repeats=2, window=4)
        guard.check("search", {"query": "docs"})
        with self.assertRaises(LoopDetected) as ctx:
            guard.check("search", {"query": "docs"})
        msg = str(ctx.exception)
        self.assertIn("search", msg)
        self.assertIn("docs", msg)
        self.assertIn("2 times", msg)

    def test_budget_exceeded_includes_call_detail(self):
        guard = BudgetGuard(max_cost_usd=1.00)
        with self.assertRaises(Exception) as ctx:
            guard.consume(cost_usd=1.50)
        msg = str(ctx.exception)
        self.assertIn("this call added", msg)
        self.assertIn("$1.5000", msg)

    def test_timeout_exceeded_includes_elapsed(self):
        import time
        guard = TimeoutGuard(max_seconds=0.01)
        guard.start()
        time.sleep(0.05)
        with self.assertRaises(Exception) as ctx:
            guard.check()
        msg = str(ctx.exception)
        self.assertIn("elapsed:", msg)


# ---------------------------------------------------------------------------
# py.typed
# ---------------------------------------------------------------------------


class TestPyTypedMarker(unittest.TestCase):
    def test_py_typed_file_exists(self):
        import agentguard
        pkg_dir = os.path.dirname(agentguard.__file__)
        self.assertTrue(os.path.exists(os.path.join(pkg_dir, "py.typed")))


# ---------------------------------------------------------------------------
# Tracer context manager
# ---------------------------------------------------------------------------


class TestTracerContextManager(unittest.TestCase):
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
        class MinimalSink:
            def emit(self, event):
                pass

        sink = MinimalSink()
        with Tracer(sink=sink) as tracer:
            with tracer.trace("test"):
                pass

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


# ---------------------------------------------------------------------------
# summarize_trace
# ---------------------------------------------------------------------------


class TestSummarizeTrace(unittest.TestCase):
    def _make_trace_file(self, events):
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
            self.assertEqual(result["spans"], 2)
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

    def test_summarize_invalid_input_type(self):
        with self.assertRaises(TypeError):
            summarize_trace(42)

    def test_summarize_real_trace(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            sink = JsonlFileSink(path)
            tracer = Tracer(sink=sink, service="test")
            with tracer.trace("agent.run") as ctx:
                ctx.event("tool.search", data={"q": "test"})
                with ctx.span("tool.lookup"):
                    ctx.event("tool.result", data={"found": True})
            result = summarize_trace(path)
            self.assertGreater(result["total_events"], 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
