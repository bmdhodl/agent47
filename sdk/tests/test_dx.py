"""Tests for SDK-2 Developer Experience features: repr, docstrings, guards param."""
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
    Recorder,
    Replayer,
    EvalSuite,
    LoopDetected,
)
from agentguard.tracing import TraceContext


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


class TestRecordingRepr(unittest.TestCase):
    def test_recorder_repr(self):
        recorder = Recorder("runs.jsonl")
        self.assertEqual(repr(recorder), "Recorder('runs.jsonl')")

    def test_replayer_repr(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            replayer = Replayer(path)
            self.assertEqual(repr(replayer), f"Replayer({path!r})")
        finally:
            os.unlink(path)


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
        # No exception — no guards configured

    def test_tracer_guards_default_empty(self):
        tracer = Tracer()
        self.assertEqual(tracer._guards, [])


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


class TestPyTypedMarker(unittest.TestCase):
    def test_py_typed_file_exists(self):
        import agentguard
        pkg_dir = os.path.dirname(agentguard.__file__)
        self.assertTrue(os.path.exists(os.path.join(pkg_dir, "py.typed")))


if __name__ == "__main__":
    unittest.main()
