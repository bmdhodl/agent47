"""One price table: current rows, dated snapshots, long-context tiers, unknown models."""
import random
from datetime import date

import pytest

from agentguard.cost import estimate_cost
from agentguard.precision_cost import (
    SOURCE_COMPUTED,
    SOURCE_OVERESTIMATE,
    _compute_from_table,
    _prompt_tokens,
    resolve_billable_cost,
)
from agentguard.price_table import (
    CEILING_PROVIDERS,
    DEFAULT_PRICE_TABLE,
    apply_long_context,
    lookup_rate,
    provider_ceiling,
)


def _usage(prompt, completion, cached=0):
    usage = {"prompt_tokens": prompt, "completion_tokens": completion,
             "total_tokens": prompt + completion}
    if cached:
        usage["prompt_tokens_details"] = {"cached_tokens": cached}
    return {"usage": usage}


@pytest.mark.parametrize("model, rates", [
    # platform.claude.com/docs/en/about-claude/pricing, read 2026-09-26:
    # (input, output, cache read, 5-minute cache write) per 1M tokens.
    ("claude-fable-5-1", (10.00, 50.00, 0.25, 12.50)),
    ("claude-fable-5", (10.00, 50.00, 1.00, 12.50)),
    ("claude-opus-5-5", (4.00, 20.00, 0.20, 5.00)),
    ("claude-opus-5", (5.00, 25.00, 0.50, 6.25)),
    ("claude-opus-4-8", (5.00, 25.00, 0.50, 6.25)),
    ("claude-sonnet-5", (2.00, 10.00, 0.20, 2.50)),
    ("claude-haiku-4-5", (1.00, 5.00, 0.10, 1.25)),
    ("claude-opus-4-20250514", (15.00, 75.00, 1.50, 18.75)),
])
def test_claude_rows_match_the_pricing_page(model, rates):
    rate = lookup_rate(DEFAULT_PRICE_TABLE, "anthropic", model)
    assert (rate["input_per_1m"], rate["output_per_1m"], rate["cached_input_per_1m"],
            rate["cache_write_per_1m"]) == rates


@pytest.mark.parametrize("provider, model, base", [
    ("openai", "gpt-4o-2024-11-20", "gpt-4o"),
    ("openai", "gpt-5.5-2026-04-23", "gpt-5.5"),
    ("anthropic", "claude-haiku-4-5-20251001", "claude-haiku-4-5"),
    ("anthropic", "claude-opus-4-1-20250805", "claude-opus-4-1"),
    ("anthropic", "claude-opus-4-5@20251101", "claude-opus-4-5"),
])
def test_dated_snapshots_price_as_their_base_model(provider, model, base):
    assert lookup_rate(DEFAULT_PRICE_TABLE, provider, model) == lookup_rate(
        DEFAULT_PRICE_TABLE, provider, base
    )
    usage = {"usage": {"input_tokens": 1000, "output_tokens": 100}}
    resolved = resolve_billable_cost(usage, model=model, provider=provider)
    assert resolved["source"] == SOURCE_COMPUTED


def test_a_snapshot_with_its_own_row_keeps_it():
    assert lookup_rate(DEFAULT_PRICE_TABLE, "openai", "gpt-4o-2024-05-13")["input_per_1m"] == 5.00


def test_gpt_5_5_long_prompt_is_repriced_on_every_path():
    # 300k prompt tokens crosses the 272k threshold: 2x input, 1.5x output.
    expected = (300_000 * 10.00 + 1_000 * 45.00) / 1_000_000
    resolved = resolve_billable_cost(_usage(300_000, 1_000), model="gpt-5.5", provider="openai")
    assert resolved["cost_usd"] == pytest.approx(expected)
    assert estimate_cost("gpt-5.5", 300_000, 1_000, provider="openai") == pytest.approx(expected)
    short = resolve_billable_cost(_usage(200_000, 1_000), model="gpt-5.5", provider="openai")
    assert short["cost_usd"] == pytest.approx((200_000 * 5.00 + 1_000 * 30.00) / 1_000_000)


def test_estimate_cost_and_resolver_read_the_same_rows():
    for (provider, model), rate in DEFAULT_PRICE_TABLE["rates"].items():
        if rate.get("free"):
            continue
        resolved = resolve_billable_cost(
            {"usage": {"input_tokens": 1000, "output_tokens": 500, "total_tokens": 1500}},
            model=model, provider=provider,
        )
        assert resolved["source"] == SOURCE_COMPUTED, (provider, model)
        if provider in ("openai", "azure", "openrouter", "litellm", "mistral", "meta"):
            expected = estimate_cost(model, 1000, 500, provider=provider)
            assert resolved["cost_usd"] == pytest.approx(expected), (provider, model)


def test_unknown_model_is_priced_at_the_provider_ceiling():
    resolved = resolve_billable_cost(_usage(10_000, 500), model="gpt-next", provider="openai")
    assert resolved["source"] == SOURCE_OVERESTIMATE
    assert resolved["breakdown"]["reason"] == "unknown_model_provider_ceiling"
    assert resolved["cost_usd"] == pytest.approx((10_000 * 30.00 + 500 * 180.00) / 1_000_000)
    # The flat high-water charge it replaces: $150 per 1M tokens of any kind.
    assert resolved["cost_usd"] < 10_500 * 150.0 / 1_000_000


@pytest.mark.parametrize("provider", ["google", "azure", "some-gateway"])
def test_providers_without_a_ceiling_keep_the_high_water_charge(provider):
    resolved = resolve_billable_cost(_usage(1_000, 1_000), model="unknown-model", provider=provider)
    assert resolved["source"] == SOURCE_OVERESTIMATE
    assert resolved["cost_usd"] == pytest.approx(2_000 * 150.0 / 1_000_000)


@pytest.mark.parametrize("provider", CEILING_PROVIDERS)
def test_ceiling_never_prices_below_a_listed_model(provider):
    ceiling = provider_ceiling(DEFAULT_PRICE_TABLE, provider)
    rows = [rate for (p, _m), rate in DEFAULT_PRICE_TABLE["rates"].items()
            if p == provider and not rate.get("free")]
    rng = random.Random(0)
    for _ in range(2000):
        tokens = {
            "input": rng.randint(0, 1_000_000),
            "output": rng.randint(0, 128_000),
            "cache_write": rng.randint(0, 200_000),
        }
        # Reasoning is a slice of output, as providers report it.
        tokens["reasoning"] = rng.randint(0, tokens["output"])
        tokens["cached"] = rng.randint(0, tokens["input"])
        tokens["total"] = sum(tokens.values())
        top, _ = _compute_from_table(tokens, ceiling, provider=provider)
        for rate in rows:
            listed, _ = _compute_from_table(
                tokens, apply_long_context(rate, _prompt_tokens(tokens, provider)),
                provider=provider,
            )
            assert top >= listed - 1e-12


def test_every_tracked_provider_has_a_past_verification_date():
    verified = DEFAULT_PRICE_TABLE["verified"]
    assert set(verified) >= {"anthropic", "openai", "google"}
    assert all(date.fromisoformat(day) <= date.today() for day in verified.values())


def test_total_only_usage_is_never_free():
    # Some gateways report only total_tokens; the split between input and output is unknown.
    usage = {"usage": {"total_tokens": 10_000}}
    unknown = resolve_billable_cost(usage, model="gpt-next", provider="openai")
    assert unknown["source"] == SOURCE_OVERESTIMATE
    assert unknown["cost_usd"] == pytest.approx(10_000 * 150.0 / 1_000_000)
    known = resolve_billable_cost(usage, model="gpt-4o", provider="openai")
    # Every token at the output rate, the higher of the two.
    assert known["cost_usd"] == pytest.approx(10_000 * 10.00 / 1_000_000)


def test_every_alias_points_at_a_rate_row():
    # lookup_rate follows one alias hop; an alias to another alias would price as unknown.
    rates = DEFAULT_PRICE_TABLE["rates"]
    assert [a for a, target in DEFAULT_PRICE_TABLE["aliases"].items() if target not in rates] == []
