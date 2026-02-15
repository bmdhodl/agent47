"""Tests for guards: LoopGuard, BudgetGuard, TimeoutGuard, FuzzyLoopGuard, RateLimitGuard."""
import json
import os
import tempfile
import time
import unittest

from agentguard.guards import (
    BaseGuard,
    BudgetExceeded,
    BudgetGuard,
    FuzzyLoopGuard,
    LoopDetected,
    LoopGuard,
    RateLimitGuard,
    TimeoutExceeded,
    TimeoutGuard,
)
from agentguard.evaluation import EvalSuite


# ---------------------------------------------------------------------------
# LoopGuard
# ---------------------------------------------------------------------------


class TestLoopGuard(unittest.TestCase):
    def test_detects_repeats(self) -> None:
        guard = LoopGuard(max_repeats=3, window=5)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        with self.assertRaises(LoopDetected):
            guard.check("search", {"q": "a"})


class TestLoopGuardWindowBehavior(unittest.TestCase):
    def test_repeats_separated_by_different_calls_pass(self) -> None:
        guard = LoopGuard(max_repeats=3, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        guard.check("lookup", {"key": "b"})
        guard.check("lookup", {"key": "c"})
        guard.check("search", {"q": "a"})  # should not raise

    def test_window_maxlen_limits_history(self) -> None:
        guard = LoopGuard(max_repeats=2, window=3)
        guard.check("a", {})
        guard.check("b", {})
        guard.check("c", {})
        guard.check("a", {})  # should not raise

    def test_exact_window_boundary(self) -> None:
        guard = LoopGuard(max_repeats=3, window=3)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        with self.assertRaises(LoopDetected):
            guard.check("search", {"q": "a"})

    def test_different_args_dont_trigger(self) -> None:
        guard = LoopGuard(max_repeats=2, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        guard.check("search", {"q": "c"})  # should not raise

    def test_reset_clears_history(self) -> None:
        guard = LoopGuard(max_repeats=2, window=4)
        guard.check("search", {"q": "a"})
        guard.reset()
        guard.check("search", {"q": "a"})  # should not raise


class TestLoopGuardAutoCheck(unittest.TestCase):
    def test_auto_check_triggers_loop_detection(self):
        guard = LoopGuard(max_repeats=2)
        guard.auto_check("tool.search", {"q": "test"})
        with self.assertRaises(LoopDetected):
            guard.auto_check("tool.search", {"q": "test"})

    def test_auto_check_different_names_ok(self):
        guard = LoopGuard(max_repeats=2)
        guard.auto_check("tool.search", {"q": "a"})
        guard.auto_check("tool.read", {"q": "b"})
        guard.auto_check("tool.search", {"q": "a"})


# ---------------------------------------------------------------------------
# BudgetGuard
# ---------------------------------------------------------------------------


class TestBudgetGuard(unittest.TestCase):
    def test_token_budget(self) -> None:
        guard = BudgetGuard(max_tokens=5)
        guard.consume(tokens=3)
        with self.assertRaises(BudgetExceeded):
            guard.consume(tokens=3)

    def test_call_budget(self) -> None:
        guard = BudgetGuard(max_calls=2)
        guard.consume(calls=1)
        guard.consume(calls=1)
        with self.assertRaises(BudgetExceeded):
            guard.consume(calls=1)

    def test_cost_budget(self) -> None:
        guard = BudgetGuard(max_cost_usd=2.00)
        guard.consume(cost_usd=1.50)
        with self.assertRaises(BudgetExceeded) as ctx:
            guard.consume(cost_usd=0.75)
        self.assertIn("$", str(ctx.exception))

    def test_cost_budget_exact_threshold(self) -> None:
        guard = BudgetGuard(max_cost_usd=1.00)
        guard.consume(cost_usd=1.00)
        guard.consume(cost_usd=0.0)
        with self.assertRaises(BudgetExceeded):
            guard.consume(cost_usd=0.01)

    def test_cost_tracks_in_state(self) -> None:
        guard = BudgetGuard(max_cost_usd=10.00)
        guard.consume(cost_usd=2.50)
        self.assertAlmostEqual(guard.state.cost_used, 2.50)
        guard.consume(cost_usd=1.25)
        self.assertAlmostEqual(guard.state.cost_used, 3.75)

    def test_cost_only_budget(self) -> None:
        guard = BudgetGuard(max_cost_usd=5.00)
        guard.consume(tokens=1000, calls=10, cost_usd=1.00)
        self.assertEqual(guard.state.tokens_used, 1000)
        self.assertEqual(guard.state.calls_used, 10)

    def test_requires_at_least_one_limit(self) -> None:
        with self.assertRaises(ValueError):
            BudgetGuard()

    def test_reset_clears_all_state(self) -> None:
        guard = BudgetGuard(max_tokens=100, max_calls=10, max_cost_usd=5.00)
        guard.consume(tokens=50, calls=5, cost_usd=2.50)
        guard.reset()
        self.assertEqual(guard.state.tokens_used, 0)
        self.assertEqual(guard.state.calls_used, 0)
        self.assertAlmostEqual(guard.state.cost_used, 0.0)
        guard.consume(tokens=50, calls=5, cost_usd=2.00)


class TestBudgetGuardInputValidation(unittest.TestCase):
    def test_string_tokens_raises_type_error(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        with self.assertRaises(TypeError) as ctx:
            guard.consume(tokens="five")  # type: ignore[arg-type]
        self.assertIn("tokens must be a number", str(ctx.exception))

    def test_string_calls_raises_type_error(self) -> None:
        guard = BudgetGuard(max_calls=10)
        with self.assertRaises(TypeError) as ctx:
            guard.consume(calls="one")  # type: ignore[arg-type]
        self.assertIn("calls must be a number", str(ctx.exception))

    def test_string_cost_raises_type_error(self) -> None:
        guard = BudgetGuard(max_cost_usd=5.00)
        with self.assertRaises(TypeError) as ctx:
            guard.consume(cost_usd="cheap")  # type: ignore[arg-type]
        self.assertIn("cost_usd must be a number", str(ctx.exception))

    def test_none_tokens_raises_type_error(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        with self.assertRaises(TypeError):
            guard.consume(tokens=None)  # type: ignore[arg-type]

    def test_float_tokens_accepted(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        guard.consume(tokens=5.5)


class TestBudgetExceededPrecision(unittest.TestCase):
    def test_cost_exceeded_uses_consistent_precision(self) -> None:
        guard = BudgetGuard(max_cost_usd=1.00)
        with self.assertRaises(BudgetExceeded) as ctx:
            guard.consume(cost_usd=1.50)
        msg = str(ctx.exception)
        self.assertIn("$1.5000", msg)
        self.assertIn("$1.0000", msg)


class TestBudgetGuardWarnAtPct(unittest.TestCase):
    def test_warning_callback_fires(self):
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=10.00,
            warn_at_pct=0.8,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(cost_usd=7.00)
        self.assertEqual(len(warnings), 0)
        guard.consume(cost_usd=2.00)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Budget warning", warnings[0])

    def test_warning_fires_once(self):
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=10.00,
            warn_at_pct=0.5,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(cost_usd=6.00)
        guard.consume(cost_usd=1.00)
        self.assertEqual(len(warnings), 1)

    def test_warning_resets_with_guard(self):
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=10.00,
            warn_at_pct=0.5,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(cost_usd=6.00)
        self.assertEqual(len(warnings), 1)
        guard.reset()
        guard.consume(cost_usd=6.00)
        self.assertEqual(len(warnings), 2)

    def test_no_warning_without_callback(self):
        guard = BudgetGuard(max_cost_usd=10.00, warn_at_pct=0.5)
        guard.consume(cost_usd=8.00)

    def test_token_warning(self):
        warnings = []
        guard = BudgetGuard(
            max_tokens=100,
            warn_at_pct=0.8,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(tokens=85)
        self.assertEqual(len(warnings), 1)
        self.assertIn("tokens", warnings[0])


# ---------------------------------------------------------------------------
# TimeoutGuard
# ---------------------------------------------------------------------------


class TestTimeoutGuard(unittest.TestCase):
    def test_no_timeout(self) -> None:
        guard = TimeoutGuard(max_seconds=10)
        guard.start()
        guard.check()

    def test_timeout_exceeded(self) -> None:
        guard = TimeoutGuard(max_seconds=0.05)
        guard.start()
        time.sleep(0.1)
        with self.assertRaises(TimeoutExceeded):
            guard.check()

    def test_check_before_start_raises(self) -> None:
        guard = TimeoutGuard(max_seconds=10)
        with self.assertRaises(RuntimeError):
            guard.check()

    def test_reset(self) -> None:
        guard = TimeoutGuard(max_seconds=0.05)
        guard.start()
        time.sleep(0.1)
        guard.reset()
        guard.start()
        guard.check()

    def test_invalid_max_seconds(self):
        with self.assertRaises(ValueError):
            TimeoutGuard(max_seconds=0)


class TestTimeoutGuardAutoCheck(unittest.TestCase):
    def test_auto_check_before_start_is_noop(self):
        guard = TimeoutGuard(max_seconds=10)
        guard.auto_check("tool.search")

    def test_auto_check_after_start(self):
        guard = TimeoutGuard(max_seconds=10)
        guard.start()
        guard.auto_check("tool.search")


class TestTimeoutGuardContextManager(unittest.TestCase):
    def test_context_manager_starts_timer(self):
        guard = TimeoutGuard(max_seconds=10)
        with guard:
            guard.check()

    def test_context_manager_raises_on_timeout(self):
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(TimeoutExceeded):
            with guard:
                time.sleep(0.05)

    def test_context_manager_no_check_if_exception(self):
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(ValueError):
            with guard:
                time.sleep(0.05)
                raise ValueError("user error")

    def test_context_manager_manual_check_inside(self):
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(TimeoutExceeded):
            with guard:
                time.sleep(0.05)
                guard.check()

    def test_context_manager_returns_self(self):
        guard = TimeoutGuard(max_seconds=10)
        with guard as g:
            self.assertIs(g, guard)


# ---------------------------------------------------------------------------
# FuzzyLoopGuard
# ---------------------------------------------------------------------------


class TestFuzzyLoopGuardFrequency(unittest.TestCase):
    def test_same_tool_different_args_triggers(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=6)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        with self.assertRaises(LoopDetected) as ctx:
            guard.check("search", {"q": "c"})
        self.assertIn("Fuzzy loop", str(ctx.exception))

    def test_different_tools_dont_trigger(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=6)
        guard.check("search", {"q": "a"})
        guard.check("lookup", {"key": "b"})
        guard.check("fetch", {"url": "c"})

    def test_window_eviction(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        guard.check("lookup", {})
        guard.check("fetch", {})
        guard.check("search", {"q": "c"})


class TestFuzzyLoopGuardAlternation(unittest.TestCase):
    def test_ababab_triggers(self):
        guard = FuzzyLoopGuard(max_tool_repeats=10, max_alternations=3, window=10)
        guard.check("search", {})
        guard.check("summarize", {})
        guard.check("search", {})
        guard.check("summarize", {})
        guard.check("search", {})
        with self.assertRaises(LoopDetected) as ctx:
            guard.check("summarize", {})
        self.assertIn("Alternation", str(ctx.exception))

    def test_no_alternation_for_varied_pattern(self):
        guard = FuzzyLoopGuard(max_tool_repeats=10, max_alternations=3, window=10)
        guard.check("search", {})
        guard.check("summarize", {})
        guard.check("lookup", {})
        guard.check("search", {})
        guard.check("summarize", {})


class TestFuzzyLoopGuardMisc(unittest.TestCase):
    def test_repr(self):
        guard = FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3, window=10)
        r = repr(guard)
        self.assertIn("FuzzyLoopGuard", r)
        self.assertIn("max_tool_repeats=5", r)

    def test_reset(self):
        guard = FuzzyLoopGuard(max_tool_repeats=2, window=4)
        guard.check("search", {})
        guard.reset()
        guard.check("search", {})

    def test_invalid_max_tool_repeats(self):
        with self.assertRaises(ValueError):
            FuzzyLoopGuard(max_tool_repeats=1)

    def test_invalid_max_alternations(self):
        with self.assertRaises(ValueError):
            FuzzyLoopGuard(max_alternations=1)

    def test_auto_check_triggers_fuzzy_detection(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3)
        guard.auto_check("tool.search", {"q": "a"})
        guard.auto_check("tool.search", {"q": "b"})
        with self.assertRaises(LoopDetected):
            guard.auto_check("tool.search", {"q": "c"})


# ---------------------------------------------------------------------------
# RateLimitGuard
# ---------------------------------------------------------------------------


class TestRateLimitGuard(unittest.TestCase):
    def test_under_limit(self):
        guard = RateLimitGuard(max_calls_per_minute=10)
        for _ in range(10):
            guard.check()
        with self.assertRaises(BudgetExceeded) as ctx:
            guard.check()
        self.assertIn("Rate limit", str(ctx.exception))

    def test_reset(self):
        guard = RateLimitGuard(max_calls_per_minute=2)
        guard.check()
        guard.check()
        guard.reset()
        guard.check()

    def test_repr(self):
        guard = RateLimitGuard(max_calls_per_minute=60)
        self.assertEqual(repr(guard), "RateLimitGuard(max_calls_per_minute=60)")

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            RateLimitGuard(max_calls_per_minute=0)

    def test_auto_check_delegates(self):
        guard = RateLimitGuard(max_calls_per_minute=2)
        guard.auto_check("tool.a")
        guard.auto_check("tool.b")
        with self.assertRaises(BudgetExceeded):
            guard.auto_check("tool.c")


# ---------------------------------------------------------------------------
# BaseGuard
# ---------------------------------------------------------------------------


class TestBaseGuard(unittest.TestCase):
    def test_auto_check_is_noop(self):
        guard = BaseGuard()
        guard.auto_check("tool.search", {"q": "test"})

    def test_reset_is_noop(self):
        guard = BaseGuard()
        guard.reset()

    def test_subclass_can_override(self):
        class CountingGuard(BaseGuard):
            def __init__(self):
                self.count = 0

            def auto_check(self, event_name, event_data=None):
                self.count += 1

            def reset(self):
                self.count = 0

        guard = CountingGuard()
        guard.auto_check("tool.search")
        guard.auto_check("tool.search")
        self.assertEqual(guard.count, 2)
        guard.reset()
        self.assertEqual(guard.count, 0)

    def test_isinstance_checks(self):
        self.assertIsInstance(LoopGuard(), BaseGuard)
        self.assertIsInstance(BudgetGuard(max_calls=10), BaseGuard)
        self.assertIsInstance(TimeoutGuard(max_seconds=10), BaseGuard)
        self.assertIsInstance(FuzzyLoopGuard(), BaseGuard)
        self.assertIsInstance(RateLimitGuard(max_calls_per_minute=10), BaseGuard)


# ---------------------------------------------------------------------------
# Tracer auto-check dispatch
# ---------------------------------------------------------------------------


class TestTracerAutoCheckDispatch(unittest.TestCase):
    def test_auto_check_called_on_events(self):
        from agentguard.tracing import Tracer

        class RecordingGuard(BaseGuard):
            def __init__(self):
                self.calls = []

            def auto_check(self, event_name, event_data=None):
                self.calls.append((event_name, event_data))

        guard = RecordingGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search", data={"q": "test"})
            ctx.event("tool.read")

        self.assertEqual(len(guard.calls), 2)
        self.assertEqual(guard.calls[0], ("tool.search", {"q": "test"}))
        self.assertEqual(guard.calls[1], ("tool.read", None))

    def test_backward_compat_check_dispatch(self):
        from agentguard.tracing import Tracer

        class OldStyleGuard:
            def __init__(self):
                self.calls = []

            def check(self, name, data=None):
                self.calls.append(name)

        guard = OldStyleGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search")

        self.assertEqual(guard.calls, ["tool.search"])

    def test_backward_compat_no_args_check(self):
        from agentguard.tracing import Tracer

        class NoArgsGuard:
            def __init__(self):
                self.called = False

            def check(self):
                self.called = True

        guard = NoArgsGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search")

        self.assertTrue(guard.called)


# ---------------------------------------------------------------------------
# EvalSuite cost / budget warnings
# ---------------------------------------------------------------------------


def _write_trace(events):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


class TestEvalCostUnder(unittest.TestCase):
    def test_passes_under_cost(self):
        events = [
            {"name": "llm.result", "data": {"cost_usd": 0.05}},
            {"name": "llm.result", "data": {"cost_usd": 0.03}},
        ]
        path = _write_trace(events)
        result = EvalSuite(path).assert_cost_under(1.00).run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_over_cost(self):
        events = [
            {"name": "llm.result", "data": {"cost_usd": 0.80}},
            {"name": "llm.result", "data": {"cost_usd": 0.30}},
        ]
        path = _write_trace(events)
        result = EvalSuite(path).assert_cost_under(1.00).run()
        os.unlink(path)
        self.assertFalse(result.passed)

    def test_top_level_cost_usd(self):
        events = [
            {"name": "llm.result", "cost_usd": 0.50, "data": {}},
        ]
        path = _write_trace(events)
        result = EvalSuite(path).assert_cost_under(1.00).run()
        os.unlink(path)
        self.assertTrue(result.passed)


class TestEvalNoBudgetWarnings(unittest.TestCase):
    def test_passes_no_warnings(self):
        events = [{"name": "agent.run", "kind": "span"}]
        path = _write_trace(events)
        result = EvalSuite(path).assert_no_budget_warnings().run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_with_warnings(self):
        events = [{"name": "guard.budget_warning", "kind": "event"}]
        path = _write_trace(events)
        result = EvalSuite(path).assert_no_budget_warnings().run()
        os.unlink(path)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
