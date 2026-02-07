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


if __name__ == "__main__":
    unittest.main()
