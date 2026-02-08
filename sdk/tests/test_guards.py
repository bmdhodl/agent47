import time
import unittest

from agentguard.guards import (
    BudgetExceeded,
    BudgetGuard,
    LoopDetected,
    LoopGuard,
    TimeoutExceeded,
    TimeoutGuard,
)


class TestLoopGuard(unittest.TestCase):
    def test_detects_repeats(self) -> None:
        guard = LoopGuard(max_repeats=3, window=5)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        with self.assertRaises(LoopDetected):
            guard.check("search", {"q": "a"})


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
        # Exactly at limit should not raise
        guard.consume(cost_usd=0.0)
        # Over limit should raise
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
        self.assertEqual(guard.state.tokens_used, 50)
        self.assertEqual(guard.state.calls_used, 5)
        self.assertAlmostEqual(guard.state.cost_used, 2.50)
        guard.reset()
        self.assertEqual(guard.state.tokens_used, 0)
        self.assertEqual(guard.state.calls_used, 0)
        self.assertAlmostEqual(guard.state.cost_used, 0.0)
        # Can consume again after reset
        guard.consume(tokens=50, calls=5, cost_usd=2.00)


class TestTimeoutGuard(unittest.TestCase):
    def test_no_timeout(self) -> None:
        guard = TimeoutGuard(max_seconds=10)
        guard.start()
        guard.check()  # should not raise

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
        guard.check()  # fresh start, should not raise


class TestBudgetGuardInputValidation(unittest.TestCase):
    def test_string_tokens_raises_type_error(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        with self.assertRaises(TypeError) as ctx:
            guard.consume(tokens="five")  # type: ignore[arg-type]
        self.assertIn("tokens must be a number", str(ctx.exception))
        self.assertIn("str", str(ctx.exception))

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

    def test_list_cost_raises_type_error(self) -> None:
        guard = BudgetGuard(max_cost_usd=5.00)
        with self.assertRaises(TypeError):
            guard.consume(cost_usd=[1.0])  # type: ignore[arg-type]

    def test_float_tokens_accepted(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        guard.consume(tokens=5.5)  # float is valid for numeric params


class TestBudgetExceededPrecision(unittest.TestCase):
    def test_cost_exceeded_uses_consistent_precision(self) -> None:
        guard = BudgetGuard(max_cost_usd=1.00)
        with self.assertRaises(BudgetExceeded) as ctx:
            guard.consume(cost_usd=1.50)
        msg = str(ctx.exception)
        # Both values should use .4f precision
        self.assertIn("$1.5000", msg)
        self.assertIn("$1.0000", msg)


class TestLoopGuardWindowBehavior(unittest.TestCase):
    def test_repeats_separated_by_different_calls_pass(self) -> None:
        """Repeated calls separated by enough different calls should not trigger."""
        guard = LoopGuard(max_repeats=3, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        # Insert different calls to push the first two out of the window
        guard.check("lookup", {"key": "b"})
        guard.check("lookup", {"key": "c"})
        # Now this "search" call should not trigger since window only has 4 items
        guard.check("search", {"q": "a"})  # should not raise

    def test_window_maxlen_limits_history(self) -> None:
        """History should be bounded by window size."""
        guard = LoopGuard(max_repeats=2, window=3)
        guard.check("a", {})
        guard.check("b", {})
        guard.check("c", {})
        # "a" should be pushed out of window
        guard.check("a", {})  # should not raise — only 1 "a" in window

    def test_exact_window_boundary(self) -> None:
        """Repeats at exact window boundary should still trigger."""
        guard = LoopGuard(max_repeats=3, window=3)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "a"})
        with self.assertRaises(LoopDetected):
            guard.check("search", {"q": "a"})

    def test_different_args_dont_trigger(self) -> None:
        """Same tool name with different args should not trigger."""
        guard = LoopGuard(max_repeats=2, window=4)
        guard.check("search", {"q": "a"})
        guard.check("search", {"q": "b"})
        guard.check("search", {"q": "c"})  # should not raise

    def test_reset_clears_history(self) -> None:
        guard = LoopGuard(max_repeats=2, window=4)
        guard.check("search", {"q": "a"})
        guard.reset()
        guard.check("search", {"q": "a"})  # should not raise — history cleared


if __name__ == "__main__":
    unittest.main()
