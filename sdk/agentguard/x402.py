"""Spend caps for x402 / USDC agent micropayments.

Agents that pay per-call via x402 (HTTP 402 + stablecoin micropayments) have a
budget surface the token guards do not cover: the wallet. A looping agent can
drain it silently at fractions of a cent per call. ``X402SpendGuard`` wraps the
outbound payment step and refuses payments that would breach a cap.

AgentGuard meters and refuses; it does not sign, settle, or speak the x402
protocol. The caller passes amounts in. No crypto dependencies.

Usage::

    from agentguard import X402SpendGuard

    guard = X402SpendGuard(max_total_usd=5.00, max_per_call_usd=0.10)
    guard.charge(0.001, "https://api.example.com/search", pay_step)
    # a runaway loop eventually raises BudgetExceeded BEFORE paying
"""
from __future__ import annotations

import math
import threading
import time
from typing import Any, Callable, Dict, Optional

from .guards import BaseGuard, BudgetExceeded

__all__ = ["X402SpendGuard"]


def _validate_amount(amount_usd: Any) -> float:
    if isinstance(amount_usd, bool) or not isinstance(amount_usd, (int, float)):
        raise TypeError(
            f"amount_usd must be a number, got {type(amount_usd).__name__}: {amount_usd!r}"
        )
    if isinstance(amount_usd, float) and not math.isfinite(amount_usd):
        raise ValueError(f"amount_usd must be finite, got {amount_usd!r}")
    if amount_usd < 0:
        raise ValueError(f"amount_usd must be non-negative, got {amount_usd!r}")
    return float(amount_usd)


class X402SpendGuard(BaseGuard):
    """Refuse x402/USDC payments that would breach a spend cap.

    Thread-safe. Reuses ``BudgetExceeded`` so existing handlers kill the run
    exactly like token budgets. Boundary semantics match ``BudgetGuard``:
    landing at a cap is allowed, going above refuses. Refusal happens BEFORE
    the payment callable runs, so a refused payment is never recorded.

    Args:
        max_total_usd: Cap on total spend. None = unlimited.
        max_per_endpoint_usd: Cap on spend per endpoint (resource URL). None = unlimited.
        max_per_call_usd: Refuse any single payment above this. None = unlimited.
        warn_at_pct: Fraction of ``max_total_usd`` to warn at, once. No-op without a total cap.
        on_warning: Callback invoked with a message when ``warn_at_pct`` is crossed.
        period: ``"day"`` resets totals at the UTC day boundary. None = never.
        now: Clock override for tests (returns epoch seconds).
    """

    def __init__(
        self,
        max_total_usd: Optional[float] = None,
        max_per_endpoint_usd: Optional[float] = None,
        max_per_call_usd: Optional[float] = None,
        warn_at_pct: Optional[float] = None,
        on_warning: Optional[Callable[[str], None]] = None,
        *,
        period: Optional[str] = None,
        now: Optional[Callable[[], float]] = None,
    ) -> None:
        if max_total_usd is None and max_per_endpoint_usd is None and max_per_call_usd is None:
            raise ValueError(
                "Provide max_total_usd, max_per_endpoint_usd, or max_per_call_usd"
            )
        if period not in (None, "day"):
            raise ValueError("period must be 'day' or None")
        if warn_at_pct is not None and not 0.0 < warn_at_pct <= 1.0:
            raise ValueError(f"warn_at_pct must be in (0.0, 1.0], got {warn_at_pct!r}")
        self._max_total_usd = max_total_usd
        self._max_per_endpoint_usd = max_per_endpoint_usd
        self._max_per_call_usd = max_per_call_usd
        self._warn_at_pct = warn_at_pct
        self._on_warning = on_warning
        self._period = period
        self._now = now if now is not None else time.time
        self._lock = threading.Lock()
        self._total_spent = 0.0
        self._spent_by_endpoint: Dict[str, float] = {}
        self._warned = False
        self._bucket = self._current_bucket()

    @property
    def total_spent_usd(self) -> float:
        """Total recorded spend in the current period."""
        with self._lock:
            self._roll_period()
            return self._total_spent

    def endpoint_spent_usd(self, endpoint: str) -> float:
        """Recorded spend for one endpoint in the current period."""
        with self._lock:
            self._roll_period()
            return self._spent_by_endpoint.get(endpoint, 0.0)

    def check(self, amount_usd: float, endpoint: str) -> None:
        """Raise ``BudgetExceeded`` if paying ``amount_usd`` would breach a cap.

        Records nothing. Call before the payment step, or use :meth:`charge`
        to check, pay, and record in one call.
        """
        amount = _validate_amount(amount_usd)
        with self._lock:
            self._roll_period()
            self._refuse_if_breach(amount, endpoint)

    def charge(
        self,
        amount_usd: float,
        endpoint: str,
        pay: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Check caps, run the payment callable, record the spend.

        Raises ``BudgetExceeded`` without calling ``pay`` if the payment would
        breach a cap. The spend is reserved before ``pay(*args, **kwargs)`` runs
        so concurrent charges cannot overshoot; if ``pay`` raises, the
        reservation rolls back and the exception propagates; a failed payment
        costs nothing. Returns whatever ``pay`` returns.
        """
        amount = _validate_amount(amount_usd)
        with self._lock:
            self._roll_period()
            self._refuse_if_breach(amount, endpoint)
            warning = self._record_locked(amount, endpoint)
        try:
            result = pay(*args, **kwargs)
        except BaseException:
            with self._lock:
                self._total_spent = max(self._total_spent - amount, 0.0)
                spent = self._spent_by_endpoint.get(endpoint, 0.0) - amount
                self._spent_by_endpoint[endpoint] = max(spent, 0.0)
                if warning is not None:
                    self._warned = False  # the crossing spend never settled
            raise
        if warning is not None and self._on_warning is not None:
            self._on_warning(warning)  # outside the lock: callbacks may re-enter
        return result

    def __repr__(self) -> str:
        return (
            f"X402SpendGuard(max_total_usd={self._max_total_usd}, "
            f"max_per_endpoint_usd={self._max_per_endpoint_usd}, "
            f"max_per_call_usd={self._max_per_call_usd})"
        )

    def reset(self) -> None:
        """Clear all recorded spend and the warning latch."""
        with self._lock:
            self._total_spent = 0.0
            self._spent_by_endpoint.clear()
            self._warned = False

    def _current_bucket(self) -> str:
        if self._period is None:
            return ""
        return time.strftime("%Y-%m-%d", time.gmtime(self._now()))

    def _roll_period(self) -> None:
        """Reset totals when the UTC day rolls over. Caller holds the lock."""
        if self._period is None:
            return
        bucket = self._current_bucket()
        if bucket != self._bucket:
            self._bucket = bucket
            self._total_spent = 0.0
            self._spent_by_endpoint.clear()
            self._warned = False

    def _refuse_if_breach(self, amount: float, endpoint: str) -> None:
        """Raise if a prospective payment of ``amount`` would breach a cap."""
        message = self._breach_message(amount, endpoint)
        if message is not None:
            raise BudgetExceeded(message)

    def _breach_message(self, amount: float, endpoint: str) -> Optional[str]:
        if self._max_per_call_usd is not None and amount > self._max_per_call_usd:
            return (
                f"x402 per-call ceiling exceeded: ${amount:.6f} > "
                f"${self._max_per_call_usd:.6f} for {endpoint}"
            )
        endpoint_spent = self._spent_by_endpoint.get(endpoint, 0.0)
        cap = self._max_per_endpoint_usd
        if cap is not None and endpoint_spent + amount > cap:
            return (
                f"x402 endpoint budget exceeded: ${endpoint_spent + amount:.6f} > "
                f"${cap:.6f} for {endpoint} "
                f"(this payment adds ${amount:.6f})"
            )
        total_cap = self._max_total_usd
        if total_cap is not None and self._total_spent + amount > total_cap:
            return (
                f"x402 total budget exceeded: ${self._total_spent + amount:.6f} > "
                f"${total_cap:.6f} (this payment adds ${amount:.6f})"
            )
        return None

    def _record_locked(self, amount: float, endpoint: str) -> Optional[str]:
        """Add spend. Returns a warning message to fire after lock release, or None."""
        self._total_spent += amount
        self._spent_by_endpoint[endpoint] = (
            self._spent_by_endpoint.get(endpoint, 0.0) + amount
        )
        cap = self._max_total_usd
        if (
            self._warn_at_pct is None
            or cap is None
            or self._warned
            or self._total_spent < self._warn_at_pct * cap
        ):
            return None
        self._warned = True
        return (
            f"x402 spend at ${self._total_spent:.6f} of ${cap:.6f} cap "
            f"({self._total_spent / cap:.0%})"
        )
