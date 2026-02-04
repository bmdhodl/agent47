import unittest

from agentguard.guards import BudgetExceeded, BudgetGuard, LoopDetected, LoopGuard


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


if __name__ == "__main__":
    unittest.main()
