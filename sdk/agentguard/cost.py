"""Cost estimation for LLM API calls.

Hardcoded pricing dict — no network calls, no dependencies.
Override with update_prices() for custom or new models.
"""
from __future__ import annotations

import threading
import warnings
from typing import Any, Dict, Optional, Tuple


class UnknownModelWarning(UserWarning):
    """Issued when estimate_cost() encounters an unrecognized model name."""
    pass

# Prices per 1K tokens: (input_price, output_price)
# Last updated: 2026-02-01
_PRICES: Dict[Tuple[str, str], Tuple[float, float]] = {
    # OpenAI
    ("openai", "gpt-4o"): (0.0025, 0.010),
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
    ("openai", "gpt-4-turbo"): (0.01, 0.03),
    ("openai", "gpt-4"): (0.03, 0.06),
    ("openai", "gpt-3.5-turbo"): (0.0005, 0.0015),
    ("openai", "o1"): (0.015, 0.06),
    ("openai", "o1-mini"): (0.003, 0.012),
    ("openai", "o3-mini"): (0.0011, 0.0044),
    # Anthropic
    ("anthropic", "claude-3-5-sonnet-20241022"): (0.003, 0.015),
    ("anthropic", "claude-3-5-haiku-20241022"): (0.0008, 0.004),
    ("anthropic", "claude-3-opus-20240229"): (0.015, 0.075),
    ("anthropic", "claude-sonnet-4-5-20250929"): (0.003, 0.015),
    ("anthropic", "claude-haiku-4-5-20251001"): (0.0008, 0.004),
    ("anthropic", "claude-opus-4-6"): (0.015, 0.075),
    # Google
    ("google", "gemini-1.5-pro"): (0.00125, 0.005),
    ("google", "gemini-1.5-flash"): (0.000075, 0.0003),
    ("google", "gemini-2.0-flash"): (0.0001, 0.0004),
    # Mistral
    ("mistral", "mistral-large-latest"): (0.002, 0.006),
    ("mistral", "mistral-small-latest"): (0.0002, 0.0006),
    # Meta (via various providers)
    ("meta", "llama-3.1-70b"): (0.00035, 0.0004),
}

LAST_UPDATED = "2026-02-01"


def estimate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    provider: Optional[str] = None,
) -> float:
    """Estimate cost in USD for a single LLM call.

    Args:
        model: Model name (e.g. "gpt-4o", "claude-3-5-sonnet-20241022").
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.
        provider: Provider name (e.g. "openai", "anthropic"). If None,
                  tries all providers to find a match.

    Returns:
        Estimated cost in USD. Returns 0.0 if model not found.
    """
    if provider:
        prices = _PRICES.get((provider, model))
        if prices:
            return (input_tokens * prices[0] + output_tokens * prices[1]) / 1000.0
    else:
        # Try all providers
        for (_p, m), prices in _PRICES.items():
            if m == model:
                return (input_tokens * prices[0] + output_tokens * prices[1]) / 1000.0
    warnings.warn(
        f"Unknown model '{model}'. Pricing data last updated {LAST_UPDATED}. "
        f"Cost estimate is $0.00. Use update_prices() to add custom pricing.",
        UnknownModelWarning,
        stacklevel=2,
    )
    return 0.0


def update_prices(overrides: Dict[Tuple[str, str], Tuple[float, float]]) -> None:
    """Override or add model pricing.

    Args:
        overrides: Dict mapping (provider, model) to (input_price/1K, output_price/1K).

    Example::

        update_prices({("openai", "gpt-5"): (0.05, 0.15)})
    """
    _PRICES.update(overrides)


class CostTracker:
    """Accumulates cost across a trace. Thread-safe.

    Usage::

        tracker = CostTracker()
        tracker.add("gpt-4o", input_tokens=500, output_tokens=200)
        tracker.add("gpt-4o", input_tokens=300, output_tokens=100)
        print(f"Total: ${tracker.total:.4f}")
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total: float = 0.0
        self._calls: list[Dict[str, Any]] = []

    def add(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        provider: Optional[str] = None,
    ) -> float:
        """Add a call's cost. Returns the cost of this individual call."""
        cost = estimate_cost(model, input_tokens, output_tokens, provider)
        with self._lock:
            self._total += cost
            self._calls.append({
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            })
        return cost

    @property
    def total(self) -> float:
        """Total accumulated cost in USD."""
        return self._total

    def to_dict(self) -> Dict[str, Any]:
        """Return summary as a dict for event data."""
        with self._lock:
            return {
                "total_cost_usd": self._total,
                "call_count": len(self._calls),
                "calls": list(self._calls),
            }
