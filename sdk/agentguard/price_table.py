"""Caller-owned versioned LLM price table for precision cost resolution.

Rates are approximate public list prices (USD per 1_000_000 tokens unless noted).
AgentGuard does NOT fetch live prices or invoices — this table is an explicit
caller-owned default you can replace via `prices=` on resolve_billable_cost.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Default high-water overestimate: ~$150 / 1M tokens (covers frontier output rates).
_DEFAULT_HIGH_WATER_PER_TOKEN = 150.0 / 1_000_000
_DEFAULT_MIN_CHARGE_USD = 0.001


# ---------------------------------------------------------------------------
# Explicit caller-owned price table (versioned)
# ---------------------------------------------------------------------------
# Rates are USD per 1_000_000 tokens unless noted. Never use a single global
# $/token for all models — each (provider, model_id) has its own rates.
# last_updated tracks when this table was last hand-verified against public
# list prices. It is still NOT invoice data.

PriceRate = Dict[str, float]
PriceKey = Tuple[str, str]
PriceTable = Dict[str, Any]


def _rate(
    input_per_1m: float,
    output_per_1m: float,
    *,
    cached_input_per_1m: Optional[float] = None,
    cache_write_per_1m: Optional[float] = None,
    reasoning_per_1m: Optional[float] = None,
    batch_discount: Optional[float] = None,
    image_per_unit: Optional[float] = None,
    free: bool = False,
) -> PriceRate:
    rate: PriceRate = {
        "input_per_1m": float(input_per_1m),
        "output_per_1m": float(output_per_1m),
    }
    if cached_input_per_1m is not None:
        rate["cached_input_per_1m"] = float(cached_input_per_1m)
    if cache_write_per_1m is not None:
        rate["cache_write_per_1m"] = float(cache_write_per_1m)
    if reasoning_per_1m is not None:
        rate["reasoning_per_1m"] = float(reasoning_per_1m)
    if batch_discount is not None:
        rate["batch_discount"] = float(batch_discount)
    if image_per_unit is not None:
        rate["image_per_unit"] = float(image_per_unit)
    if free:
        rate["free"] = 1.0
    return rate


# Built from public list prices (approximate). Prefer provider-reported cost when
# available. Multiply legacy estimate_cost per-1k rates by 1000 for per-1m.
DEFAULT_PRICE_TABLE: PriceTable = {
    "version": "2026.07.15",
    "last_updated": "2026-07-15",
    "overestimate": {
        "min_charge_usd": _DEFAULT_MIN_CHARGE_USD,
        "high_water_per_token": _DEFAULT_HIGH_WATER_PER_TOKEN,
    },
    "rates": {
        # OpenAI — standard in/out; cached input typically ~50% of input
        ("openai", "gpt-4o"): _rate(2.50, 10.00, cached_input_per_1m=1.25),
        ("openai", "gpt-4o-mini"): _rate(0.15, 0.60, cached_input_per_1m=0.075),
        ("openai", "gpt-4-turbo"): _rate(10.00, 30.00, cached_input_per_1m=5.00),
        ("openai", "gpt-4"): _rate(30.00, 60.00),
        ("openai", "gpt-3.5-turbo"): _rate(0.50, 1.50),
        ("openai", "o1"): _rate(15.00, 60.00, cached_input_per_1m=7.50),
        ("openai", "o1-mini"): _rate(3.00, 12.00, cached_input_per_1m=1.50),
        ("openai", "o3-mini"): _rate(1.10, 4.40, cached_input_per_1m=0.55),
        ("openai", "gpt-5.5"): _rate(5.00, 30.00, cached_input_per_1m=2.50),
        ("openai", "gpt-5.5-pro"): _rate(30.00, 180.00, cached_input_per_1m=15.00),
        ("openai", "gpt-5.4"): _rate(2.50, 15.00, cached_input_per_1m=1.25),
        ("openai", "gpt-5.4-mini"): _rate(0.75, 4.50, cached_input_per_1m=0.375),
        ("openai", "gpt-5.4-nano"): _rate(0.20, 1.25, cached_input_per_1m=0.10),
        ("openai", "text-embedding-3-small"): _rate(0.02, 0.0),
        ("openai", "text-embedding-3-large"): _rate(0.13, 0.0),
        # Anthropic — cache read ~10% of input; cache write ~1.25x input
        ("anthropic", "claude-3-5-sonnet-20241022"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-3-5-haiku-20241022"): _rate(
            0.80, 4.00, cached_input_per_1m=0.08, cache_write_per_1m=1.00
        ),
        ("anthropic", "claude-3-opus-20240229"): _rate(
            15.00, 75.00, cached_input_per_1m=1.50, cache_write_per_1m=18.75
        ),
        ("anthropic", "claude-sonnet-4-20250514"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-sonnet-4-5-20250929"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-sonnet-4-5"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-sonnet-4-6"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-haiku-4-5-20251001"): _rate(
            1.00, 5.00, cached_input_per_1m=0.10, cache_write_per_1m=1.25
        ),
        ("anthropic", "claude-opus-4-20250515"): _rate(
            15.00, 75.00, cached_input_per_1m=1.50, cache_write_per_1m=18.75
        ),
        ("anthropic", "claude-opus-4-6"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-5"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-7"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        # Google
        ("google", "gemini-1.5-pro"): _rate(1.25, 5.00, cached_input_per_1m=0.3125),
        ("google", "gemini-1.5-flash"): _rate(0.075, 0.30, cached_input_per_1m=0.01875),
        ("google", "gemini-2.0-flash"): _rate(0.10, 0.40, cached_input_per_1m=0.025),
        ("google", "gemini-2.5-pro"): _rate(1.25, 10.00, cached_input_per_1m=0.3125),
        ("google", "gemini-2.5-flash"): _rate(0.30, 2.50, cached_input_per_1m=0.075),
        ("google", "gemini-2.5-flash-lite"): _rate(0.10, 0.40, cached_input_per_1m=0.025),
        # Azure OpenAI — same list family; prefer Azure billed cost when present
        ("azure", "gpt-4o"): _rate(2.50, 10.00, cached_input_per_1m=1.25),
        ("azure", "gpt-4o-mini"): _rate(0.15, 0.60, cached_input_per_1m=0.075),
        # Example gateway with published markup (not OpenAI list rates)
        ("openrouter", "openai/gpt-4o"): _rate(2.75, 11.00, cached_input_per_1m=1.375),
        ("litellm", "gpt-4o"): _rate(2.50, 10.00, cached_input_per_1m=1.25),
        # Local / free
        ("local", "llama-3.1-8b"): _rate(0.0, 0.0, free=True),
        ("ollama", "llama3.1"): _rate(0.0, 0.0, free=True),
        ("local", "free"): _rate(0.0, 0.0, free=True),
        # Mistral / Meta
        ("mistral", "mistral-large-latest"): _rate(2.00, 6.00),
        ("mistral", "mistral-small-latest"): _rate(0.20, 0.60),
        ("meta", "llama-3.1-70b"): _rate(0.35, 0.40),
    },
    # Normalized aliases: exact (provider, model_id) miss → alias target
    "aliases": {
        ("openai", "gpt-4o-2024-08-06"): ("openai", "gpt-4o"),
        ("openai", "gpt-4o-2024-11-20"): ("openai", "gpt-4o"),
        ("openai", "gpt-4o-mini-2024-07-18"): ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-5-sonnet-latest"): ("anthropic", "claude-3-5-sonnet-20241022"),
        ("anthropic", "claude-3-5-haiku-latest"): ("anthropic", "claude-3-5-haiku-20241022"),
        ("azure_openai", "gpt-4o"): ("azure", "gpt-4o"),
        ("azure-openai", "gpt-4o"): ("azure", "gpt-4o"),
    },
}


def get_default_prices() -> PriceTable:
    """Return a shallow copy of the built-in versioned price table."""
    table = dict(DEFAULT_PRICE_TABLE)
    table["rates"] = dict(DEFAULT_PRICE_TABLE["rates"])
    table["aliases"] = dict(DEFAULT_PRICE_TABLE["aliases"])
    table["overestimate"] = dict(DEFAULT_PRICE_TABLE["overestimate"])
    return table


