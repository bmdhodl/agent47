"""Cost estimation for LLM API calls.

Reads the shared price table in ``agentguard.price_table`` — no network calls,
no dependencies.
"""
from __future__ import annotations

import logging
import threading
import warnings
from typing import Any, Dict, List, Optional

from agentguard.price_table import DEFAULT_PRICE_TABLE, apply_long_context, lookup_rate

logger = logging.getLogger("agentguard.cost")


class UnknownModelWarning(UserWarning):
    """Issued when estimate_cost() encounters an unrecognized model name."""
    pass


LAST_UPDATED = DEFAULT_PRICE_TABLE["last_updated"]


def _rate_for(model: str, provider: Optional[str]) -> Optional[Dict[str, float]]:
    """Rate row from the shared price table; without a provider, the first provider listing it."""
    if provider:
        return lookup_rate(DEFAULT_PRICE_TABLE, provider, model)
    for listed in dict.fromkeys(p for p, _ in DEFAULT_PRICE_TABLE["rates"]):
        rate = lookup_rate(DEFAULT_PRICE_TABLE, listed, model)
        if rate is not None:
            return rate
    return None


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
    rate = _rate_for(model, provider)
    if rate is not None:
        if rate.get("free"):
            return 0.0
        rate = apply_long_context(rate, input_tokens)
        return (input_tokens * rate["input_per_1m"] + output_tokens * rate["output_per_1m"]) / 1_000_000
    message = (
        f"Unknown model '{model}'. Pricing data last updated {LAST_UPDATED}. "
        "Cost estimate is $0.00."
    )
    logger.warning(message)
    warnings.warn(message, UnknownModelWarning, stacklevel=2)
    return 0.0


class CostTracker:
    """Internal cost accumulator used by TraceContext.cost property.

    Thread-safe. Tracks per-call costs and maintains a running total.
    Not part of the public API — use BudgetGuard for budget enforcement.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: List[Dict[str, Any]] = []
        self._total: float = 0.0

    @property
    def total(self) -> float:
        """Total accumulated cost in USD."""
        return self._total

    def add(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        provider: Optional[str] = None,
    ) -> float:
        """Add a call's cost. Returns the cost of this call."""
        cost = estimate_cost(model, input_tokens, output_tokens, provider)
        with self._lock:
            self._calls.append({
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            })
            self._total += cost
        return cost

    def to_dict(self) -> Dict[str, Any]:
        """Return a summary dict."""
        with self._lock:
            return {
                "total_cost_usd": self._total,
                "call_count": len(self._calls),
                "calls": list(self._calls),
            }
