"""Tests for SDK-4 smarter guards: FuzzyLoopGuard, RateLimitGuard, warn_at_pct."""
import json
import os
import tempfile
import time
import unittest

from agentguard.guards import (
    BudgetExceeded,
    BudgetGuard,
    FuzzyLoopGuard,
    LoopDetected,
    RateLimitGuard,
)
from agentguard.evaluation import EvalSuite


class TestFuzzyLoopGuardFrequency(unittest.TestCase):
    def test_same_tool_different_args_triggers(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=6)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        with self.assertRaises(LoopDetected) as ctx:
            guard.check("search", {"q": "c"})
        self.assertIn("Fuzzy loop", str(ctx.exception))
        self.assertIn("search", str(ctx.exception))

    def test_different_tools_dont_trigger(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=6)
        guard.check("search", {"q": "a"})
        guard.check("lookup", {"key": "b"})
        guard.check("fetch", {"url": "c"})  # should not raise

    def test_window_eviction(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        guard.check("lookup", {})
        guard.check("fetch", {})
        # "search" should be partially evicted from window
        guard.check("search", {"q": "c"})  # should not raise (only 1 in window)


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
        guard.check("lookup", {})  # breaks alternation
        guard.check("search", {})
        guard.check("summarize", {})  # should not raise


class TestFuzzyLoopGuardRepr(unittest.TestCase):
    def test_repr(self):
        guard = FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3, window=10)
        r = repr(guard)
        self.assertIn("FuzzyLoopGuard", r)
        self.assertIn("max_tool_repeats=5", r)

    def test_reset(self):
        guard = FuzzyLoopGuard(max_tool_repeats=2, window=4)
        guard.check("search", {})
        guard.reset()
        guard.check("search", {})  # should not raise after reset


class TestFuzzyLoopGuardValidation(unittest.TestCase):
    def test_invalid_max_tool_repeats(self):
        with self.assertRaises(ValueError):
            FuzzyLoopGuard(max_tool_repeats=1)

    def test_invalid_max_alternations(self):
        with self.assertRaises(ValueError):
            FuzzyLoopGuard(max_alternations=1)


class TestBudgetGuardWarnAtPct(unittest.TestCase):
    def test_warning_callback_fires(self):
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=10.00,
            warn_at_pct=0.8,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(cost_usd=7.00)  # 70% — no warning
        self.assertEqual(len(warnings), 0)
        guard.consume(cost_usd=2.00)  # 90% — should warn
        self.assertEqual(len(warnings), 1)
        self.assertIn("Budget warning", warnings[0])

    def test_warning_fires_once(self):
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=10.00,
            warn_at_pct=0.5,
            on_warning=lambda msg: warnings.append(msg),
        )
        guard.consume(cost_usd=6.00)  # 60% — triggers
        guard.consume(cost_usd=1.00)  # 70% — should NOT trigger again
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
        guard.consume(cost_usd=8.00)  # should not raise

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


class TestRateLimitGuard(unittest.TestCase):
    def test_under_limit(self):
        guard = RateLimitGuard(max_calls_per_minute=10)
        for _ in range(10):
            guard.check()
        # 10th call should work, 11th should not
        with self.assertRaises(BudgetExceeded) as ctx:
            guard.check()
        self.assertIn("Rate limit", str(ctx.exception))

    def test_reset(self):
        guard = RateLimitGuard(max_calls_per_minute=2)
        guard.check()
        guard.check()
        guard.reset()
        guard.check()  # should not raise after reset

    def test_repr(self):
        guard = RateLimitGuard(max_calls_per_minute=60)
        self.assertEqual(repr(guard), "RateLimitGuard(max_calls_per_minute=60)")

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            RateLimitGuard(max_calls_per_minute=0)


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


def _write_trace(events):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


if __name__ == "__main__":
    unittest.main()
