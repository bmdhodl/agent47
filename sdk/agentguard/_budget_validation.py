"""Boundary validation shared by in-memory and persisted budgets."""
from __future__ import annotations

import math
from typing import Any, Dict, Optional


def validate_budget_config(max_tokens: Any, max_calls: Any, max_cost_usd: Any,
                           warn_at_pct: Any, on_warning: Any) -> None:
    for name, value in (("max_tokens", max_tokens), ("max_calls", max_calls),
                        ("max_cost_usd", max_cost_usd)):
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a number")
            if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
                raise ValueError(f"{name} must be finite and non-negative")
    if warn_at_pct is not None:
        if isinstance(warn_at_pct, bool) or not isinstance(warn_at_pct, (int, float)):
            raise TypeError("warn_at_pct must be a number")
        if not 0 <= warn_at_pct <= 1:
            raise ValueError("warn_at_pct must be between 0 and 1")
    if on_warning is not None and not callable(on_warning):
        raise TypeError("on_warning must be callable")


def validate_budget_state(current: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from .state import StateStoreError
    if current is not None and not isinstance(current, dict):
        raise StateStoreError("stored budget must be an object")
    st = dict(current) if current else {}
    for field in ("tokens_used", "calls_used", "cost_used"):
        value = st.get(field, 0)
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or value < 0
                or (isinstance(value, float) and not math.isfinite(value))):
            raise StateStoreError(f"stored budget {field} must be finite and non-negative")
    return st


def validate_consumption(tokens: Any, calls: Any, cost_usd: Any) -> None:
    if not isinstance(tokens, (int, float)):
        raise TypeError(
            f"tokens must be a number, got {type(tokens).__name__}: {tokens!r}"
        )
    if not isinstance(calls, (int, float)):
        raise TypeError(
            f"calls must be a number, got {type(calls).__name__}: {calls!r}"
        )
    if not isinstance(cost_usd, (int, float)):
        raise TypeError(
            f"cost_usd must be a number, got {type(cost_usd).__name__}: {cost_usd!r}"
        )
    # A non-finite value (NaN/inf) would silently defeat budget enforcement:
    # NaN poisons the running total and `NaN > max` is always False, so the
    # guard would never fire again. Negative values reduce running totals and
    # can similarly bypass enforcement (e.g. consume(cost_usd=-100) after spend).
    # Reject both classes loudly before any state mutation.
    for _name, _val in (("tokens", tokens), ("calls", calls), ("cost_usd", cost_usd)):
        if isinstance(_val, float) and not math.isfinite(_val):
            raise ValueError(f"{_name} must be finite, got {_val!r}")
        if _val < 0:
            raise ValueError(f"{_name} must be non-negative, got {_val!r}")
