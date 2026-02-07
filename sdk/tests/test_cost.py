import unittest

from agentguard.cost import CostTracker, estimate_cost, update_prices


class TestEstimateCost(unittest.TestCase):
    def test_known_model_with_provider(self) -> None:
        cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500, provider="openai")
        # (1000 * 0.0025 + 500 * 0.010) / 1000 = 0.0025 + 0.005 = 0.0075
        self.assertAlmostEqual(cost, 0.0075, places=6)

    def test_known_model_without_provider(self) -> None:
        cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
        self.assertAlmostEqual(cost, 0.0075, places=6)

    def test_unknown_model_returns_zero(self) -> None:
        cost = estimate_cost("nonexistent-model", input_tokens=1000, output_tokens=500)
        self.assertEqual(cost, 0.0)

    def test_anthropic_model(self) -> None:
        cost = estimate_cost("claude-3-5-sonnet-20241022", input_tokens=1000, output_tokens=500, provider="anthropic")
        # (1000 * 0.003 + 500 * 0.015) / 1000 = 0.003 + 0.0075 = 0.0105
        self.assertAlmostEqual(cost, 0.0105, places=6)

    def test_zero_tokens(self) -> None:
        cost = estimate_cost("gpt-4o", input_tokens=0, output_tokens=0, provider="openai")
        self.assertEqual(cost, 0.0)

    def test_wrong_provider(self) -> None:
        cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500, provider="anthropic")
        self.assertEqual(cost, 0.0)


class TestUpdatePrices(unittest.TestCase):
    def test_add_custom_model(self) -> None:
        update_prices({("custom", "my-model"): (0.01, 0.02)})
        cost = estimate_cost("my-model", input_tokens=1000, output_tokens=1000, provider="custom")
        # (1000 * 0.01 + 1000 * 0.02) / 1000 = 0.01 + 0.02 = 0.03
        self.assertAlmostEqual(cost, 0.03, places=6)

    def test_override_existing_model(self) -> None:
        original = estimate_cost("gpt-3.5-turbo", input_tokens=1000, output_tokens=1000, provider="openai")
        update_prices({("openai", "gpt-3.5-turbo"): (0.001, 0.002)})
        updated = estimate_cost("gpt-3.5-turbo", input_tokens=1000, output_tokens=1000, provider="openai")
        self.assertNotEqual(original, updated)
        # Restore original
        update_prices({("openai", "gpt-3.5-turbo"): (0.0005, 0.0015)})


class TestCostTracker(unittest.TestCase):
    def test_accumulates_cost(self) -> None:
        tracker = CostTracker()
        c1 = tracker.add("gpt-4o", input_tokens=1000, output_tokens=500, provider="openai")
        c2 = tracker.add("gpt-4o", input_tokens=2000, output_tokens=1000, provider="openai")
        self.assertGreater(c1, 0)
        self.assertGreater(c2, 0)
        self.assertAlmostEqual(tracker.total, c1 + c2, places=6)

    def test_to_dict(self) -> None:
        tracker = CostTracker()
        tracker.add("gpt-4o", input_tokens=1000, output_tokens=500, provider="openai")
        d = tracker.to_dict()
        self.assertIn("total_cost_usd", d)
        self.assertIn("call_count", d)
        self.assertIn("calls", d)
        self.assertEqual(d["call_count"], 1)
        self.assertEqual(len(d["calls"]), 1)

    def test_empty_tracker(self) -> None:
        tracker = CostTracker()
        self.assertEqual(tracker.total, 0.0)
        d = tracker.to_dict()
        self.assertEqual(d["call_count"], 0)

    def test_unknown_model_adds_zero(self) -> None:
        tracker = CostTracker()
        cost = tracker.add("fake-model", input_tokens=1000, output_tokens=1000)
        self.assertEqual(cost, 0.0)
        self.assertEqual(tracker.total, 0.0)


if __name__ == "__main__":
    unittest.main()
