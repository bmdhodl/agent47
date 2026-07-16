"""Tests for maximum-precision cost resolution and BudgetGuard wiring.

Drives the shipped ``resolve_billable_cost`` / ``consume_billable`` entry points
directly — no re-implementation of cost math inside the tests.
"""
from __future__ import annotations

import os
import unittest
from typing import Any, Dict, List
from unittest import mock

from agentguard import (
    ALLOWED_SOURCES,
    DEFAULT_PRICE_TABLE,
    BudgetExceeded,
    BudgetGuard,
    CostResolutionError,
    consume_billable,
    get_default_prices,
    resolve_billable_cost,
)
from agentguard.precision_cost import SOURCE_COMPUTED, SOURCE_OVERESTIMATE, SOURCE_PROVIDER, SOURCE_ZERO

from tests.fixtures.usage_payloads import (
    ANTHROPIC_SONNET_USAGE,
    FAILED_WITH_USAGE,
    GATEWAY_BILLED_COST,
    MISSING_USAGE,
    OPENAI_GPT4O_USAGE,
    OPENAI_WITH_PROVIDER_COST,
    STREAMING_FINAL_USAGE,
)


def _gpt4o_table_cost(input_tokens: int, output_tokens: int, cached: int = 0) -> float:
    """Expected compute for openai/gpt-4o from DEFAULT_PRICE_TABLE rates."""
    rates = DEFAULT_PRICE_TABLE["rates"][("openai", "gpt-4o")]
    if cached and cached <= input_tokens:
        uncached = input_tokens - cached
    else:
        uncached = input_tokens
    return (
        uncached * rates["input_per_1m"]
        + output_tokens * rates["output_per_1m"]
        + cached * rates["cached_input_per_1m"]
    ) / 1_000_000


class TestResolveBillableCostKnownModel(unittest.TestCase):
    def test_known_model_compute_matches_table_math(self) -> None:
        resolved = resolve_billable_cost(
            OPENAI_GPT4O_USAGE,
            model="gpt-4o",
            provider="openai",
            prices=DEFAULT_PRICE_TABLE,
        )
        self.assertEqual(resolved["source"], SOURCE_COMPUTED)
        self.assertIn(resolved["source"], ALLOWED_SOURCES)
        expected = _gpt4o_table_cost(1000, 500, cached=200)
        self.assertAlmostEqual(resolved["cost_usd"], expected, places=10)
        self.assertEqual(resolved["tokens"]["input"], 1000)
        self.assertEqual(resolved["tokens"]["output"], 500)
        self.assertEqual(resolved["tokens"]["cached"], 200)
        self.assertEqual(resolved["tokens"]["total"], 1500)

    def test_cached_tokens_reduce_computed_cost_vs_full_input(self) -> None:
        with_cache = resolve_billable_cost(
            OPENAI_GPT4O_USAGE,
            model="gpt-4o",
            provider="openai",
        )
        no_cache_payload = {
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
            }
        }
        without_cache = resolve_billable_cost(
            no_cache_payload,
            model="gpt-4o",
            provider="openai",
        )
        self.assertEqual(with_cache["source"], SOURCE_COMPUTED)
        self.assertEqual(without_cache["source"], SOURCE_COMPUTED)
        self.assertLess(with_cache["cost_usd"], without_cache["cost_usd"])


class TestProviderCostPreferred(unittest.TestCase):
    def test_provider_numeric_cost_preferred_over_table(self) -> None:
        resolved = resolve_billable_cost(
            OPENAI_WITH_PROVIDER_COST,
            model="gpt-4o",
            provider="openai",
        )
        self.assertEqual(resolved["source"], SOURCE_PROVIDER)
        self.assertAlmostEqual(resolved["cost_usd"], 0.042, places=6)
        # Table compute would differ
        table_cost = _gpt4o_table_cost(1000, 500)
        self.assertNotAlmostEqual(resolved["cost_usd"], table_cost, places=6)


class TestUnknownModelFailLoud(unittest.TestCase):
    def test_strict_unknown_raises(self) -> None:
        payload = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            }
        }
        with self.assertRaises(CostResolutionError):
            resolve_billable_cost(
                payload,
                model="totally-unknown-model-xyz",
                provider="openai",
                strict=True,
            )

    def test_strict_missing_usage_raises(self) -> None:
        with self.assertRaises(CostResolutionError):
            resolve_billable_cost(
                MISSING_USAGE,
                model="mystery-model-xyz",
                provider="openai",
                strict=True,
            )

    def test_non_strict_unknown_uses_overestimate_not_zero(self) -> None:
        payload = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }
        resolved = resolve_billable_cost(
            payload,
            model="totally-unknown-model-xyz",
            provider="openai",
            strict=False,
        )
        self.assertEqual(resolved["source"], SOURCE_OVERESTIMATE)
        self.assertGreater(resolved["cost_usd"], 0.0)

    def test_strict_precision_env_flag(self) -> None:
        payload = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            }
        }
        with mock.patch.dict(os.environ, {"STRICT_PRECISION": "1"}):
            with self.assertRaises(CostResolutionError):
                resolve_billable_cost(
                    payload,
                    model="unknown-env-strict",
                    provider="openai",
                    strict=False,
                )


class TestRetryAndStreaming(unittest.TestCase):
    def test_two_retry_attempts_consume_twice(self) -> None:
        budget = BudgetGuard(max_cost_usd=10.0, max_tokens=100_000, max_calls=100)
        costs: List[float] = []
        for _ in range(2):
            resolved = consume_billable(
                budget,
                OPENAI_GPT4O_USAGE,
                model="gpt-4o",
                provider="openai",
            )
            costs.append(resolved["cost_usd"])
        self.assertEqual(len(costs), 2)
        self.assertAlmostEqual(sum(costs), budget.state.cost_used, places=10)
        self.assertEqual(budget.state.calls_used, 2)

    def test_streaming_final_usage_billed_once(self) -> None:
        budget = BudgetGuard(max_cost_usd=5.0, max_calls=10)
        # Partial chunks must not be passed to resolve — only final usage.
        resolved = consume_billable(
            budget,
            STREAMING_FINAL_USAGE,
            model="gpt-4o-mini",
            provider="openai",
        )
        self.assertEqual(resolved["source"], SOURCE_COMPUTED)
        self.assertEqual(budget.state.calls_used, 1)
        self.assertAlmostEqual(budget.state.cost_used, resolved["cost_usd"], places=10)

    def test_failed_call_with_usage_still_billed(self) -> None:
        resolved = resolve_billable_cost(
            FAILED_WITH_USAGE,
            model="gpt-4o",
            provider="openai",
        )
        self.assertEqual(resolved["source"], SOURCE_COMPUTED)
        self.assertGreater(resolved["cost_usd"], 0.0)


class TestGoalAttributionNoDoubleCount(unittest.TestCase):
    def test_parent_child_goal_rolls_once(self) -> None:
        budget = BudgetGuard(max_cost_usd=10.0, max_tokens=100_000, max_calls=50)
        resolved_costs: List[float] = []

        with budget.goal("parent", verifier=lambda: True) as parent:
            parent.attempt()
            r_parent = consume_billable(
                budget,
                {"usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}},
                model="gpt-4o",
                provider="openai",
            )
            resolved_costs.append(r_parent["cost_usd"])

            with budget.goal("child", verifier=lambda: True) as child:
                child.attempt()
                r_child = consume_billable(
                    budget,
                    {"usage": {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}},
                    model="gpt-4o",
                    provider="openai",
                )
                resolved_costs.append(r_child["cost_usd"])

        # Child spend rolls into parent ledger once (sub_goals), not in parent.calls
        self.assertAlmostEqual(child.cost_usd, r_child["cost_usd"], places=10)
        self.assertAlmostEqual(parent.own_cost_usd, r_parent["cost_usd"], places=10)
        self.assertAlmostEqual(
            parent.cost_usd,
            r_parent["cost_usd"] + r_child["cost_usd"],
            places=10,
        )
        self.assertEqual(len(parent.calls), 1)
        self.assertEqual(len(child.calls), 1)
        # Session budget equals sum of resolved costs (property)
        self.assertAlmostEqual(budget.state.cost_used, sum(resolved_costs), places=10)


class TestToolOnlyAndLocalZero(unittest.TestCase):
    def test_tool_only_zero(self) -> None:
        resolved = resolve_billable_cost(
            None,
            model="tool-search",
            provider="local",
            billable_llm=False,
        )
        self.assertEqual(resolved["source"], SOURCE_ZERO)
        self.assertEqual(resolved["cost_usd"], 0.0)

    def test_free_local_model_zero(self) -> None:
        resolved = resolve_billable_cost(
            {"usage": {"prompt_tokens": 1000, "completion_tokens": 100, "total_tokens": 1100}},
            model="llama-3.1-8b",
            provider="local",
        )
        self.assertEqual(resolved["source"], SOURCE_ZERO)
        self.assertEqual(resolved["cost_usd"], 0.0)


class TestPriceTable(unittest.TestCase):
    def test_versioned_with_last_updated(self) -> None:
        table = get_default_prices()
        self.assertIn("version", table)
        self.assertIn("last_updated", table)
        self.assertIsInstance(table["last_updated"], str)
        self.assertTrue(table["rates"])
        # No single global $/token key for all models
        self.assertNotIn("global_per_token", table)
        self.assertNotIn("default_per_token", table)

    def test_alias_lookup(self) -> None:
        payload = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }
        resolved = resolve_billable_cost(
            payload,
            model="gpt-4o-2024-08-06",
            provider="openai",
        )
        self.assertEqual(resolved["source"], SOURCE_COMPUTED)
        self.assertGreater(resolved["cost_usd"], 0.0)

    def test_price_miss_under_dollar_cap_not_zero(self) -> None:
        budget = BudgetGuard(max_cost_usd=1.0, max_calls=5)
        resolved = consume_billable(
            budget,
            {"usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}},
            model="unknown-priced-model",
            provider="openai",
            strict=False,
        )
        self.assertEqual(resolved["source"], SOURCE_OVERESTIMATE)
        self.assertGreater(budget.state.cost_used, 0.0)


class TestCrossingCallAttributed(unittest.TestCase):
    def test_budget_exceeded_includes_crossing_call(self) -> None:
        budget = BudgetGuard(max_cost_usd=0.001, max_calls=10)
        with self.assertRaises(BudgetExceeded):
            consume_billable(
                budget,
                OPENAI_GPT4O_USAGE,
                model="gpt-4o",
                provider="openai",
            )
        # Crossing call still attributed to state before raise
        self.assertGreater(budget.state.cost_used, 0.001)
        self.assertEqual(budget.state.calls_used, 1)


class TestPropertySumConsumeEqualsResolved(unittest.TestCase):
    def test_sum_consume_equals_sum_resolved(self) -> None:
        budget = BudgetGuard(max_cost_usd=100.0, max_tokens=1_000_000, max_calls=100)
        events = [
            (OPENAI_GPT4O_USAGE, "gpt-4o", "openai"),
            (ANTHROPIC_SONNET_USAGE, "claude-3-5-sonnet-20241022", "anthropic"),
            (GATEWAY_BILLED_COST, "openai/gpt-4o", "openrouter"),
            (STREAMING_FINAL_USAGE, "gpt-4o-mini", "openai"),
        ]
        resolved_sum = 0.0
        for payload, model, provider in events:
            r = consume_billable(budget, payload, model=model, provider=provider)
            resolved_sum += r["cost_usd"]
        self.assertAlmostEqual(budget.state.cost_used, resolved_sum, places=10)
        self.assertEqual(budget.state.calls_used, len(events))

    def test_strict_no_silent_proceed_missing_usage_and_cost(self) -> None:
        with self.assertRaises(CostResolutionError):
            resolve_billable_cost(
                MISSING_USAGE,
                model="mystery-model-xyz",
                provider="openai",
                strict=True,
            )


class TestGoldenFixtures(unittest.TestCase):
    def test_openai_fixture_computed(self) -> None:
        r = resolve_billable_cost(
            OPENAI_GPT4O_USAGE, model="gpt-4o", provider="openai"
        )
        self.assertEqual(r["source"], SOURCE_COMPUTED)
        self.assertGreater(r["cost_usd"], 0.0)

    def test_anthropic_fixture_computed(self) -> None:
        r = resolve_billable_cost(
            ANTHROPIC_SONNET_USAGE,
            model="claude-3-5-sonnet-20241022",
            provider="anthropic",
        )
        self.assertEqual(r["source"], SOURCE_COMPUTED)
        self.assertGreater(r["cost_usd"], 0.0)
        self.assertEqual(r["tokens"]["cached"], 200)
        self.assertEqual(r["tokens"]["cache_write"], 50)

    def test_gateway_fixture_provider_billed(self) -> None:
        r = resolve_billable_cost(
            GATEWAY_BILLED_COST,
            model="openai/gpt-4o",
            provider="openrouter",
        )
        self.assertEqual(r["source"], SOURCE_PROVIDER)
        self.assertAlmostEqual(r["cost_usd"], 0.055, places=6)


class TestConsumeLogFields(unittest.TestCase):
    def test_consume_log_has_required_fields(self) -> None:
        budget = BudgetGuard(max_cost_usd=5.0, max_calls=5)
        r = consume_billable(
            budget,
            OPENAI_GPT4O_USAGE,
            model="gpt-4o",
            provider="openai",
        )
        log = r["consume_log"]
        for key in (
            "model",
            "provider",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
            "cost_usd",
            "source_of_cost",
        ):
            self.assertIn(key, log)
        self.assertEqual(log["request_id"], "chatcmpl-fixture-openai-001")
        self.assertIn(log["source_of_cost"], ALLOWED_SOURCES)


class TestNoDoubleConsumePatchPath(unittest.TestCase):
    def test_emit_llm_result_uses_resolver_once(self) -> None:
        """Instrument path resolves once and calls budget.consume once."""
        from agentguard.instrument import _emit_llm_result

        class _Ctx:
            def __init__(self) -> None:
                self.events: List[Dict[str, Any]] = []

            def event(self, name: str, data=None, cost_usd=None) -> None:
                self.events.append({"name": name, "data": data, "cost_usd": cost_usd})

        budget = BudgetGuard(max_cost_usd=10.0, max_calls=10)
        ctx = _Ctx()
        _emit_llm_result(
            ctx,
            budget,
            "gpt-4o",
            "openai",
            OPENAI_GPT4O_USAGE["usage"],
            response=OPENAI_GPT4O_USAGE,
        )
        self.assertEqual(budget.state.calls_used, 1)
        self.assertGreater(budget.state.cost_used, 0.0)
        # Only one llm.result event
        llm_events = [e for e in ctx.events if e["name"] == "llm.result"]
        self.assertEqual(len(llm_events), 1)
        self.assertEqual(llm_events[0]["data"]["source_of_cost"], SOURCE_COMPUTED)


if __name__ == "__main__":
    unittest.main()
