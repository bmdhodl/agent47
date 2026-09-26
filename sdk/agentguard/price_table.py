"""Caller-owned versioned LLM price table for precision cost resolution.

Rates are approximate public list prices (USD per 1_000_000 tokens unless noted).
AgentGuard does NOT fetch live prices or invoices — this table is an explicit
caller-owned default you can replace via `prices=` on resolve_billable_cost.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional, Tuple

# Default high-water overestimate: ~$150 / 1M tokens (covers frontier output rates).
_DEFAULT_HIGH_WATER_PER_TOKEN = 150.0 / 1_000_000
_DEFAULT_MIN_CHARGE_USD = 0.001


# ---------------------------------------------------------------------------
# Explicit caller-owned price table (versioned)
# ---------------------------------------------------------------------------
# Rates are USD per 1_000_000 tokens unless noted. Never use a single global
# $/token for all models — each (provider, model_id) has its own rates.
# "verified" records, per provider, the day its rows were last checked against
# that provider's published price page. It is still NOT invoice data.

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
    long_context: Optional[Tuple[int, float, float]] = None,
    free: bool = False,
) -> PriceRate:
    """One model's rates. ``long_context`` is (prompt tokens above which the
    whole request is repriced, input multiplier, output multiplier)."""
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
    if long_context is not None:
        above, input_multiplier, output_multiplier = long_context
        rate["long_context_above"] = float(above)
        rate["long_context_input_multiplier"] = float(input_multiplier)
        rate["long_context_output_multiplier"] = float(output_multiplier)
    if free:
        rate["free"] = 1.0
    return rate


# Built from public list prices (approximate). Prefer provider-reported cost when
# available. Multiply legacy estimate_cost per-1k rates by 1000 for per-1m.
DEFAULT_PRICE_TABLE: PriceTable = {
    "version": "2026.09.26",
    "last_updated": "2026-09-26",
    # Anthropic: platform.claude.com/docs/en/about-claude/pricing, read 2026-09-26.
    # OpenAI and Google rows were last checked 2026-07-15; their pages are not
    # reachable from the environment that made the 2026-09-26 update.
    "verified": {
        "anthropic": "2026-09-26",
        "openai": "2026-07-15",
        "google": "2026-07-15",
    },
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
        # gpt-5.5 prompts over 272k input tokens bill at 2x input, 1.5x output.
        ("openai", "gpt-5.5"): _rate(
            5.00, 30.00, cached_input_per_1m=2.50, long_context=(272_000, 2.0, 1.5)
        ),
        ("openai", "gpt-5.5-pro"): _rate(30.00, 180.00, cached_input_per_1m=15.00),
        ("openai", "gpt-5.4"): _rate(2.50, 15.00, cached_input_per_1m=1.25),
        ("openai", "gpt-5.4-mini"): _rate(0.75, 4.50, cached_input_per_1m=0.375),
        ("openai", "gpt-5.4-nano"): _rate(0.20, 1.25, cached_input_per_1m=0.10),
        ("openai", "gpt-5.4-pro"): _rate(30.00, 180.00),
        ("openai", "gpt-5.3-codex"): _rate(1.75, 14.00),
        # Older snapshot priced above the gpt-4o alias; dated ids otherwise fall
        # back to their base model.
        ("openai", "gpt-4o-2024-05-13"): _rate(5.00, 15.00),
        ("openai", "text-embedding-3-small"): _rate(0.02, 0.0),
        ("openai", "text-embedding-3-large"): _rate(0.13, 0.0),
        # Anthropic — 5-minute cache write 1.25x input; cache read 0.1x input,
        # except Fable 5.1 / Mythos 5.1 (0.025x) and Opus 5.5 (0.05x).
        ("anthropic", "claude-fable-5-1"): _rate(
            10.00, 50.00, cached_input_per_1m=0.25, cache_write_per_1m=12.50
        ),
        ("anthropic", "claude-mythos-5-1"): _rate(
            10.00, 50.00, cached_input_per_1m=0.25, cache_write_per_1m=12.50
        ),
        ("anthropic", "claude-fable-5"): _rate(
            10.00, 50.00, cached_input_per_1m=1.00, cache_write_per_1m=12.50
        ),
        ("anthropic", "claude-mythos-5"): _rate(
            10.00, 50.00, cached_input_per_1m=1.00, cache_write_per_1m=12.50
        ),
        ("anthropic", "claude-opus-5-5"): _rate(
            4.00, 20.00, cached_input_per_1m=0.20, cache_write_per_1m=5.00
        ),
        ("anthropic", "claude-opus-5"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-8"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-7"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-6"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-5"): _rate(
            5.00, 25.00, cached_input_per_1m=0.50, cache_write_per_1m=6.25
        ),
        ("anthropic", "claude-opus-4-1"): _rate(
            15.00, 75.00, cached_input_per_1m=1.50, cache_write_per_1m=18.75
        ),
        ("anthropic", "claude-opus-4-20250514"): _rate(
            15.00, 75.00, cached_input_per_1m=1.50, cache_write_per_1m=18.75
        ),
        ("anthropic", "claude-sonnet-5"): _rate(
            2.00, 10.00, cached_input_per_1m=0.20, cache_write_per_1m=2.50
        ),
        ("anthropic", "claude-sonnet-4-6"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-sonnet-4-5"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-sonnet-4-20250514"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-haiku-4-5"): _rate(
            1.00, 5.00, cached_input_per_1m=0.10, cache_write_per_1m=1.25
        ),
        ("anthropic", "claude-3-5-sonnet-20241022"): _rate(
            3.00, 15.00, cached_input_per_1m=0.30, cache_write_per_1m=3.75
        ),
        ("anthropic", "claude-3-5-haiku-20241022"): _rate(
            0.80, 4.00, cached_input_per_1m=0.08, cache_write_per_1m=1.00
        ),
        ("anthropic", "claude-3-opus-20240229"): _rate(
            15.00, 75.00, cached_input_per_1m=1.50, cache_write_per_1m=18.75
        ),
        # Google
        ("google", "gemini-1.5-pro"): _rate(1.25, 5.00, cached_input_per_1m=0.3125),
        ("google", "gemini-1.5-flash"): _rate(0.075, 0.30, cached_input_per_1m=0.01875),
        ("google", "gemini-2.0-flash"): _rate(0.10, 0.40, cached_input_per_1m=0.025),
        ("google", "gemini-2.5-pro"): _rate(
            1.25, 10.00, cached_input_per_1m=0.3125, long_context=(200_000, 2.0, 1.5)
        ),
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
        ("anthropic", "claude-opus-4-0"): ("anthropic", "claude-opus-4-20250514"),
        ("anthropic", "claude-sonnet-4-0"): ("anthropic", "claude-sonnet-4-20250514"),
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


# A trailing release date: gpt-4o-2024-08-06, claude-opus-4-1-20250805,
# claude-opus-4-5@20251101 (Vertex).
_SNAPSHOT_SUFFIX = re.compile(r"^(.+?)[-@](\d{4}-\d{2}-\d{2}|\d{8})$")

# An unknown model from one of these providers is priced at that provider's
# highest listed rates. Google is left out: its listed rows are older than
# Gemini 3.1 Pro, whose long-context rate ($4 / $18) is above them.
CEILING_PROVIDERS = ("anthropic", "openai")

_INPUT_SIDE = ("input_per_1m", "cached_input_per_1m", "cache_write_per_1m")
_OUTPUT_SIDE = ("output_per_1m", "reasoning_per_1m")


def _find(rates: Mapping[Any, Any], aliases: Mapping[Any, Any], provider: str, model: str):
    for key in ((provider, model), (provider, model.lower())):
        if key in rates:
            return rates[key]
        target = aliases.get(key)
        if isinstance(target, tuple) and target in rates:
            return rates[target]
    model_l = model.lower()
    for (p, m), rate in rates.items():
        if str(p).lower() == provider and str(m).lower() == model_l:
            return rate
    for (p, m), target in aliases.items():
        if str(p).lower() == provider and str(m).lower() == model_l and target in rates:
            return rates[target]
    return None


def lookup_rate(prices: PriceTable, provider: str, model: str) -> Optional[PriceRate]:
    """Rate row for (provider, model): exact, alias, then the undated base model."""
    rates: Mapping[Any, Any] = prices.get("rates") or {}
    aliases: Mapping[Any, Any] = prices.get("aliases") or {}
    provider_l = (provider or "").strip().lower()
    model_id = (model or "").strip()
    rate = _find(rates, aliases, provider_l, model_id)
    if rate is None:
        snapshot = _SNAPSHOT_SUFFIX.match(model_id)
        if snapshot:
            rate = _find(rates, aliases, provider_l, snapshot.group(1))
    return dict(rate) if rate is not None else None


def _full_rate(rate: Mapping[str, float]) -> Dict[str, float]:
    """Fill the defaults _compute_from_table applies to missing cache/reasoning rates."""
    full = dict(rate)
    full.setdefault("cached_input_per_1m", full["input_per_1m"])
    full.setdefault("cache_write_per_1m", full["input_per_1m"] * 1.25)
    full.setdefault("reasoning_per_1m", full["output_per_1m"])
    return full


def apply_long_context(rate: PriceRate, prompt_tokens: int) -> PriceRate:
    """Reprice the whole request when its prompt exceeds the row's long-context threshold."""
    above = rate.get("long_context_above")
    if above is None or prompt_tokens <= above:
        return rate
    adjusted = _full_rate(rate)
    for key in _INPUT_SIDE:
        adjusted[key] *= rate["long_context_input_multiplier"]
    for key in _OUTPUT_SIDE:
        adjusted[key] *= rate["long_context_output_multiplier"]
    return adjusted


def provider_ceiling(prices: PriceTable, provider: str) -> Optional[PriceRate]:
    """Highest listed rate of each kind across a provider's rows, long-context included.

    Returns None for providers outside CEILING_PROVIDERS or without rows. A model
    priced above every listed row is still under-counted; keep rows current.
    """
    provider_l = (provider or "").strip().lower()
    if provider_l not in CEILING_PROVIDERS:
        return None
    ceiling: Dict[str, float] = {}
    for (p, _m), rate in (prices.get("rates") or {}).items():
        if str(p).lower() != provider_l or rate.get("free"):
            continue
        full = apply_long_context(rate, int(rate.get("long_context_above", 0)) + 1)
        for key, value in _full_rate(full).items():
            if key in _INPUT_SIDE or key in _OUTPUT_SIDE:
                ceiling[key] = max(ceiling.get(key, 0.0), value)
    return ceiling or None
