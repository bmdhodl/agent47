"""Tests targeting specific coverage gaps to reach 95%+.

Each test targets lines identified as uncovered in the coverage report.
"""
import json
import os
import tempfile
import time
import unittest

from agentguard.guards import (
    BudgetExceeded,
    BudgetGuard,
    LoopGuard,
    RateLimitGuard,
    TimeoutGuard,
)
from agentguard.tracing import Tracer, StdoutSink


# ---------------------------------------------------------------------------
# guards.py gaps
# ---------------------------------------------------------------------------


class TestLoopGuardValidation(unittest.TestCase):
    """Cover guards.py lines 112, 114 — constructor validation."""

    def test_max_repeats_too_low(self):
        with self.assertRaises(ValueError):
            LoopGuard(max_repeats=1)

    def test_max_repeats_zero(self):
        with self.assertRaises(ValueError):
            LoopGuard(max_repeats=0)

    def test_window_less_than_max_repeats(self):
        with self.assertRaises(ValueError):
            LoopGuard(max_repeats=3, window=2)


class TestTimeoutGuardValidation(unittest.TestCase):
    """Cover guards.py line 333 — constructor validation."""

    def test_max_seconds_zero(self):
        with self.assertRaises(ValueError):
            TimeoutGuard(max_seconds=0)

    def test_max_seconds_negative(self):
        with self.assertRaises(ValueError):
            TimeoutGuard(max_seconds=-1)


class TestBudgetGuardWarning(unittest.TestCase):
    """Cover guards.py lines 270, 276, 281-282 — warning threshold branches."""

    def test_token_warning(self):
        """Trigger on_warning callback via token threshold."""
        warnings = []
        bg = BudgetGuard(max_tokens=100, warn_at_pct=0.8, on_warning=warnings.append)
        bg.consume(tokens=85)
        self.assertEqual(len(warnings), 1)
        self.assertIn("tokens", warnings[0])

    def test_call_warning(self):
        """Trigger on_warning callback via call threshold."""
        warnings = []
        bg = BudgetGuard(max_calls=10, warn_at_pct=0.8, on_warning=warnings.append)
        for _ in range(9):
            bg.consume(calls=1)
        self.assertEqual(len(warnings), 1)
        self.assertIn("calls", warnings[0])

    def test_cost_warning(self):
        """Trigger on_warning callback via cost threshold."""
        warnings = []
        bg = BudgetGuard(max_cost_usd=1.0, warn_at_pct=0.8, on_warning=warnings.append)
        bg.consume(cost_usd=0.85)
        self.assertEqual(len(warnings), 1)
        self.assertIn("cost", warnings[0])

    def test_no_warning_below_threshold(self):
        """No warning when below threshold."""
        warnings = []
        bg = BudgetGuard(max_tokens=100, warn_at_pct=0.8, on_warning=warnings.append)
        bg.consume(tokens=50)
        self.assertEqual(len(warnings), 0)


class TestRateLimitGuardExpiry(unittest.TestCase):
    """Cover guards.py line 504 — timestamp expiry in deque."""

    def test_expired_timestamps_cleaned(self):
        """Old timestamps are cleaned up on check()."""
        rlg = RateLimitGuard(max_calls_per_minute=100)
        for _ in range(5):
            rlg.check()
        # Backdate timestamps to simulate expiry
        with rlg._lock:
            rlg._timestamps.clear()
            past = time.monotonic() - 120
            for _ in range(5):
                rlg._timestamps.append(past)
        # Next check cleans old ones
        rlg.check()
        with rlg._lock:
            self.assertEqual(len(rlg._timestamps), 1)


# ---------------------------------------------------------------------------
# tracing.py gaps
# ---------------------------------------------------------------------------


class TestTracerGuardFallback(unittest.TestCase):
    """Cover tracing.py lines 377-378 — guard with incompatible check()."""

    def test_guard_with_no_check_args(self):
        """Guard.check() with no args exercises the fallback path."""
        class NoArgGuard:
            def check(self):
                pass

        sink = StdoutSink()
        tracer = Tracer(sink=sink, guards=[NoArgGuard()])
        with tracer.trace("test") as ctx:
            ctx.event("step")

    def test_guard_with_incompatible_check(self):
        """Guard.check() that raises TypeError is silently ignored."""
        class BadGuard:
            def check(self, *args, **kwargs):
                raise TypeError("bad")

        sink = StdoutSink()
        tracer = Tracer(sink=sink, guards=[BadGuard()])
        with tracer.trace("test") as ctx:
            ctx.event("step")


# ---------------------------------------------------------------------------
# evaluation.py gaps
# ---------------------------------------------------------------------------


class TestEvalSuiteEdgeCases(unittest.TestCase):
    """Cover evaluation.py lines 82, 188, 202, 214, 220, 348, 401."""

    def _make_trace_file(self, events):
        """Helper: write events to a temp JSONL file."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        )
        for e in events:
            f.write(json.dumps(e) + "\n")
        f.close()
        return f.name

    def test_events_property(self):
        """Cover line 82 — .events property returns a copy."""
        from agentguard.evaluation import EvalSuite

        path = self._make_trace_file([
            {"kind": "span", "phase": "start", "name": "test"},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.events
            self.assertEqual(len(result), 1)
            result.append({"fake": True})
            self.assertEqual(len(suite.events), 1)
        finally:
            os.unlink(path)

    def test_summarize_trace_with_malformed_jsonl(self):
        """Cover line 401 — _load_events skips bad JSON lines."""
        from agentguard.evaluation import summarize_trace

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"kind": "span", "phase": "start", "name": "a"}\n')
            f.write("not json\n")
            f.write('{"kind": "event", "phase": "emit", "name": "b"}\n')
            path = f.name

        try:
            result = summarize_trace(path)
            self.assertEqual(result["total_events"], 2)
        finally:
            os.unlink(path)

    def test_summarize_trace_with_llm_and_empty_lines(self):
        """Cover line 348 (llm_calls counting) and 401 (empty lines)."""
        from agentguard.evaluation import summarize_trace

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"kind": "span", "phase": "start", "name": "llm.call"}\n')
            f.write("\n")  # empty line — covers line 401
            f.write('{"kind": "span", "phase": "end", "name": "llm.call", "duration_ms": 500}\n')
            f.write('{"kind": "event", "phase": "emit", "name": "guard.loop_detected"}\n')
            path = f.name

        try:
            result = summarize_trace(path)
            self.assertEqual(result["total_events"], 3)
            self.assertEqual(result["llm_calls"], 1)
            self.assertEqual(result["loop_detections"], 1)
        finally:
            os.unlink(path)

    def test_assert_tool_called_with_prefix(self):
        """Cover line 188 — tool call count with prefix matching."""
        from agentguard.evaluation import EvalSuite

        path = self._make_trace_file([
            {"kind": "event", "phase": "emit", "name": "tool.result"},
            {"kind": "span", "phase": "start", "name": "tool.search"},
            {"kind": "event", "phase": "emit", "name": "tool.search.execute"},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_tool_called("search", min_times=1).run()
            self.assertTrue(result.passed)
        finally:
            os.unlink(path)

    def test_assert_budget_under_pass(self):
        """Cover budget assertion passing with tokens."""
        from agentguard.evaluation import EvalSuite

        path = self._make_trace_file([
            {"kind": "event", "phase": "emit", "name": "llm.call",
             "data": {"token_usage": {"total_tokens": 50}}},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_budget_under(tokens=1000).run()
            self.assertTrue(result.passed)
        finally:
            os.unlink(path)

    def test_assert_budget_under_with_calls(self):
        """Cover lines 106, 202, 214, 220 — calls-based budget assertion."""
        from agentguard.evaluation import EvalSuite

        # Pass: tool calls under limit
        path = self._make_trace_file([
            {"kind": "span", "phase": "start", "name": "tool.search"},
            {"kind": "span", "phase": "end", "name": "tool.search"},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_budget_under(calls=10).run()
            self.assertTrue(result.passed)
        finally:
            os.unlink(path)

        # Fail: tool calls over limit
        path = self._make_trace_file([
            {"kind": "span", "phase": "start", "name": "tool.a"},
            {"kind": "span", "phase": "start", "name": "tool.b"},
            {"kind": "span", "phase": "start", "name": "tool.c"},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_budget_under(calls=2).run()
            self.assertFalse(result.passed)
        finally:
            os.unlink(path)

    def test_assert_budget_under_fail(self):
        """Cover line 220 — budget_under assertion failing (tokens)."""
        from agentguard.evaluation import EvalSuite

        path = self._make_trace_file([
            {"kind": "event", "phase": "emit", "name": "llm.call",
             "data": {"token_usage": {"total_tokens": 5000}}},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_budget_under(tokens=100).run()
            self.assertFalse(result.passed)
        finally:
            os.unlink(path)

    def test_assert_cost_under_fail(self):
        """Cover cost assertion failing."""
        from agentguard.evaluation import EvalSuite

        path = self._make_trace_file([
            {"kind": "event", "phase": "emit", "name": "llm.call",
             "data": {"cost_usd": 5.0}},
        ])
        try:
            suite = EvalSuite(path)
            result = suite.assert_cost_under(1.0).run()
            self.assertFalse(result.passed)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# setup.py gaps
# ---------------------------------------------------------------------------


class TestSetupAutoPatching(unittest.TestCase):
    """Cover setup.py lines 173-174, 180-182, 198."""

    def test_init_without_openai_installed(self):
        """init() works when openai/anthropic are not installed."""
        import agentguard

        agentguard.shutdown()
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            agentguard.init(trace_file=path, auto_patch=True)
            tracer = agentguard.get_tracer()
            self.assertIsNotNone(tracer)
            agentguard.shutdown()
        finally:
            os.unlink(path)

    def test_shutdown_without_init(self):
        """shutdown() is safe to call without init()."""
        import agentguard
        agentguard.shutdown()


class TestSetupWithApiKey(unittest.TestCase):
    """Cover setup.py lines 111-113 — HttpSink creation."""

    def test_init_creates_http_sink(self):
        import agentguard

        agentguard.shutdown()
        agentguard.init(
            api_key="ag_test_key_for_coverage",
            service="test-coverage",
            auto_patch=False,
        )
        tracer = agentguard.get_tracer()
        self.assertIsNotNone(tracer)
        from agentguard.sinks.http import HttpSink
        self.assertIsInstance(tracer._sink, HttpSink)
        agentguard.shutdown()


# ---------------------------------------------------------------------------
# cli.py gaps (testable parts — _summarize and _report)
# ---------------------------------------------------------------------------


class TestCliSummarize(unittest.TestCase):
    """Cover cli.py _summarize function."""

    def test_summarize_valid_file(self):
        from agentguard.cli import _summarize

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(json.dumps({"kind": "span", "phase": "start", "name": "a"}) + "\n")
            f.write(json.dumps({"kind": "event", "phase": "emit", "name": "b"}) + "\n")
            f.write(json.dumps({"kind": "span", "phase": "end", "name": "a"}) + "\n")
            path = f.name

        try:
            _summarize(path)
        finally:
            os.unlink(path)

    def test_summarize_with_bad_json_and_empty_lines(self):
        """Cover cli.py lines 20, 23-24 — empty lines and bad JSON."""
        from agentguard.cli import _summarize

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"kind": "span", "phase": "start", "name": "a"}\n')
            f.write("\n")  # empty line — covers line 20
            f.write("bad json\n")  # covers lines 23-24
            f.write('{"kind": "event", "phase": "emit", "name": "b"}\n')
            path = f.name

        try:
            _summarize(path)
        finally:
            os.unlink(path)


class TestCliReport(unittest.TestCase):
    """Cover cli.py _report function."""

    def test_report_text_and_json(self):
        from agentguard.cli import _report

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(json.dumps({
                "kind": "span", "phase": "start", "name": "agent.run",
                "ts": "2026-01-01T00:00:00Z",
            }) + "\n")
            f.write(json.dumps({
                "kind": "event", "phase": "emit", "name": "tool.search",
                "data": {"cost_usd": 0.05},
            }) + "\n")
            f.write(json.dumps({
                "kind": "span", "phase": "end", "name": "agent.run",
                "ts": "2026-01-01T00:00:01Z", "duration_ms": 1000,
            }) + "\n")
            path = f.name

        try:
            _report(path)
            _report(path, as_json=True)
        finally:
            os.unlink(path)

    def test_report_empty_file(self):
        """Cover cli.py lines 53-57 — empty events in _report."""
        from agentguard.cli import _report

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            path = f.name

        try:
            _report(path)  # text output with no events
            _report(path, as_json=True)  # json output with no events
        finally:
            os.unlink(path)

    def test_report_with_bad_json_and_empty_lines(self):
        """Cover cli.py lines 46, 49-50 — bad JSON in _report."""
        from agentguard.cli import _report

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write("\n")  # empty line — covers line 46
            f.write("bad json\n")  # covers lines 49-50
            f.write('{"kind": "event", "phase": "emit", "name": "x"}\n')
            path = f.name

        try:
            _report(path)
        finally:
            os.unlink(path)

    def test_report_with_loop_guard_hit(self):
        """Cover cli.py loop guard triggered branch."""
        from agentguard.cli import _report

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(json.dumps({
                "kind": "event", "phase": "emit",
                "name": "guard.loop_detected",
            }) + "\n")
            path = f.name

        try:
            _report(path)
        finally:
            os.unlink(path)


class TestCliEval(unittest.TestCase):
    """Cover cli.py line 127 — _eval with failing assertion."""

    def test_eval_failure_exits(self):
        from agentguard.cli import _eval

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            # Event with an error will fail assert_no_errors
            f.write(json.dumps({
                "kind": "event", "phase": "emit", "name": "x",
                "error": {"message": "boom"},
            }) + "\n")
            path = f.name

        try:
            with self.assertRaises(SystemExit) as cm:
                _eval(path)
            self.assertEqual(cm.exception.code, 1)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# langgraph integration gap
# ---------------------------------------------------------------------------


class TestLanggraphNonSerializable(unittest.TestCase):
    """Cover langgraph.py line 144 — non-serializable state values."""

    def test_summarize_state_with_non_serializable(self):
        from agentguard.integrations.langgraph import _summarize_state

        class Custom:
            def __repr__(self):
                return "Custom()"

        state = {"key": Custom(), "normal": "value"}
        result = _summarize_state(state)
        self.assertEqual(result["normal"], "value")
        self.assertIn("Custom()", result["key"])


# ---------------------------------------------------------------------------
# crewai integration gaps
# ---------------------------------------------------------------------------


class TestCrewaiEdgeCases(unittest.TestCase):
    """Cover crewai.py lines 167, 175, 178."""

    def test_extract_tool_output_none(self):
        from agentguard.integrations.crewai import _extract_tool_output
        result = _extract_tool_output(None)
        self.assertIsNone(result)

    def test_extract_raw_output_object(self):
        from agentguard.integrations.crewai import _extract_raw_output

        class FakeOutput:
            raw_output = "hello from crewai"

        result = _extract_raw_output(FakeOutput())
        self.assertEqual(result, "hello from crewai")

    def test_extract_raw_output_dict(self):
        from agentguard.integrations.crewai import _extract_raw_output
        result = _extract_raw_output({"raw": "dict output"})
        self.assertEqual(result, "dict output")

    def test_extract_task_description_none(self):
        """Cover crewai.py line 167 — no description attribute."""
        from agentguard.integrations.crewai import _extract_task_description
        result = _extract_task_description(42)
        self.assertIsNone(result)

    def test_extract_raw_output_none(self):
        """Cover crewai.py line 178 — no raw/raw_output/dict."""
        from agentguard.integrations.crewai import _extract_raw_output
        result = _extract_raw_output(42)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# atracing.py gaps — async guard fallback
# ---------------------------------------------------------------------------


class TestAsyncTracerGuardFallback(unittest.TestCase):
    """Cover atracing.py lines 232-235 — async guard check fallback."""

    def test_async_guard_with_no_check_args(self):
        """Guard.check() with no args exercises the async fallback path."""
        import asyncio
        from agentguard.atracing import AsyncTracer

        class NoArgGuard:
            def check(self):
                pass

        sink = StdoutSink()
        tracer = AsyncTracer(sink=sink, guards=[NoArgGuard()])

        async def run():
            async with tracer.trace("test") as ctx:
                ctx.event("step")

        asyncio.run(run())

    def test_async_guard_with_incompatible_check(self):
        """Guard.check() that raises TypeError is silently ignored (async)."""
        import asyncio
        from agentguard.atracing import AsyncTracer

        class BadGuard:
            def check(self, *args, **kwargs):
                raise TypeError("bad")

        sink = StdoutSink()
        tracer = AsyncTracer(sink=sink, guards=[BadGuard()])

        async def run():
            async with tracer.trace("test") as ctx:
                ctx.event("step")

        asyncio.run(run())


# ---------------------------------------------------------------------------
# instrument.py gaps — trace_agent with **kwargs
# ---------------------------------------------------------------------------


class TestTraceAgentKwargs(unittest.TestCase):
    """Cover instrument.py lines 65-72, 91 — wrapper path for **kwargs."""

    def test_trace_agent_with_kwargs_function(self):
        """trace_agent on a function with **kwargs injects _trace_ctx."""
        from agentguard.instrument import trace_agent

        sink = StdoutSink()
        tracer = Tracer(sink=sink, service="test")

        @trace_agent(tracer)
        def my_agent(x, **kwargs):
            ctx = kwargs.get("_trace_ctx")
            return x + 1

        result = my_agent(5)
        self.assertEqual(result, 6)

    def test_trace_agent_with_kwargs_exception(self):
        """trace_agent wrapper handles exceptions with **kwargs."""
        from agentguard.instrument import trace_agent

        sink = StdoutSink()
        tracer = Tracer(sink=sink, service="test")

        @trace_agent(tracer)
        def failing_agent(**kwargs):
            raise ValueError("test error")

        with self.assertRaises(ValueError):
            failing_agent()

    def test_trace_agent_with_trace_ctx_param(self):
        """trace_agent on a function that declares _trace_ctx parameter."""
        from agentguard.instrument import trace_agent

        sink = StdoutSink()
        tracer = Tracer(sink=sink, service="test")

        @trace_agent(tracer)
        def my_agent(x, _trace_ctx=None):
            self.assertIsNotNone(_trace_ctx)
            return x * 2

        result = my_agent(3)
        self.assertEqual(result, 6)


# ---------------------------------------------------------------------------
# http.py gaps — repr and empty batch
# ---------------------------------------------------------------------------


class TestHttpSinkEdgeCases(unittest.TestCase):
    """Cover http.py lines 267, 348 and SSRF edge cases."""

    def test_repr(self):
        """Cover line 348 — __repr__."""
        from agentguard.sinks.http import HttpSink

        sink = HttpSink(
            url="https://example.com/ingest",
            api_key="ag_test",
        )
        r = repr(sink)
        self.assertIn("HttpSink", r)
        self.assertIn("example.com", r)
        sink.shutdown()

    def test_send_empty_batch(self):
        """Cover line 267 — _send with empty batch is no-op."""
        from agentguard.sinks.http import HttpSink

        sink = HttpSink(
            url="https://example.com/ingest",
            api_key="ag_test",
        )
        sink._send([])  # Should return immediately
        sink.shutdown()

    def test_validate_url_unresolvable_hostname(self):
        """Cover http.py lines 91-93 — DNS resolution failure."""
        from agentguard.sinks.http import _validate_url

        # Hostname that can't resolve — should pass (allow future resolution)
        _validate_url("https://thisdomaindoesnotexist.invalid/ingest")

    def test_validate_url_hostname_resolves_to_private(self):
        """Cover http.py line 97 — hostname resolves to private IP."""
        from agentguard.sinks.http import _validate_url

        with self.assertRaises(ValueError) as ctx:
            _validate_url("http://localhost/ingest")
        self.assertIn("private/reserved", str(ctx.exception))

    def test_validate_url_invalid_idna_hostname(self):
        """Cover http.py lines 72-73 — IDNA encoding failure."""
        from agentguard.sinks.http import _validate_url

        # Hostname with characters that fail IDNA encoding
        with self.assertRaises(ValueError) as ctx:
            _validate_url("https://\ud800example.com/ingest")
        self.assertIn("invalid characters", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
