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
