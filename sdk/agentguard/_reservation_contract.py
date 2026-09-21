"""Private local reservation and reconciliation model (AG-03).

This is the executable contract for the store-backed reservation path.
It is not a public API. ``BudgetGuard.check()`` and ``consume()`` do not call
it. Sync non-streaming OpenAI calls with a ``StateStore`` do, via
``_reservation_path``. Unknown provider outcomes never silently free holds.

Operations: ``reserve``, ``commit``, ``cancel``, ``mark_unresolved``,
``recover_crash``. The ledger is meant to run inside an existing
``StateStore.update`` mutator after ``BudgetGuard._lock``, matching current
lock order: process lock, then store lock. Do not invert that order.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional

from ._budget_validation import validate_budget_state
from .guards import BudgetExceeded
from .state import StateStoreError

STATUS_RESERVED = "reserved"
STATUS_COMMITTED = "committed"
STATUS_CANCELLED = "cancelled"
STATUS_UNRESOLVED = "unresolved"
HOLD_STATUSES = frozenset({STATUS_RESERVED, STATUS_UNRESOLVED})
KNOWN_STATUSES = HOLD_STATUSES | {STATUS_COMMITTED, STATUS_CANCELLED}


class ReservationContractError(ValueError):
    """Protocol violation: illegal transition, missing evidence, or bad bounds."""


class MissingBound(ReservationContractError):
    """A token or dollar cap was set but the request did not supply an upper bound."""


def can_claim_invoice_cap() -> bool:
    """Provider invoices stay with the provider. This ledger is not an invoice cap."""
    return False


def _require_number(name: str, value: Any, *, allow_none: bool = False) -> Any:
    if value is None:
        if allow_none:
            return None
        raise ReservationContractError(f"{name} is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReservationContractError(f"{name} must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ReservationContractError(f"{name} must be finite")
    if value < 0:
        raise ReservationContractError(f"{name} must be non-negative")
    return value


def _validate_reservation(record: Any) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise StateStoreError("stored reservation must be an object")
    status = record.get("status")
    if status not in KNOWN_STATUSES:
        raise StateStoreError(f"stored reservation status is invalid: {status!r}")
    rec = dict(record)
    rec["calls"] = int(_require_number("calls", rec.get("calls", 1)))
    rec["tokens_bound"] = _require_number(
        "tokens_bound", rec.get("tokens_bound"), allow_none=True
    )
    rec["cost_bound"] = _require_number(
        "cost_bound", rec.get("cost_bound"), allow_none=True
    )
    version = rec.get("price_table_version")
    if version is not None and not isinstance(version, str):
        raise StateStoreError("stored reservation price_table_version must be a string")
    return rec


class ReservationLedger:
    """In-memory view of one StateStore period bucket.

    ``tokens_used`` / ``calls_used`` / ``cost_used`` remain settled totals so
    existing ``consume()`` records stay readable. Holds live only in
    ``reservations``.
    """

    def __init__(
        self,
        *,
        max_tokens: Optional[int] = None,
        max_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        period_bucket: str = "",
        tokens_used: int = 0,
        calls_used: int = 0,
        cost_used: float = 0.0,
        reservations: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        if max_tokens is None and max_calls is None and max_cost_usd is None:
            raise ValueError("Provide max_tokens, max_calls, or max_cost_usd")
        self.max_tokens = max_tokens
        self.max_calls = max_calls
        self.max_cost_usd = max_cost_usd
        self.period_bucket = period_bucket
        self.tokens_used = int(tokens_used)
        self.calls_used = int(calls_used)
        self.cost_used = float(cost_used)
        self.reservations: Dict[str, Dict[str, Any]] = dict(reservations or {})

    @classmethod
    def from_store_state(
        cls,
        current: Optional[Mapping[str, Any]],
        *,
        max_tokens: Optional[int] = None,
        max_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        period_bucket: str = "",
    ) -> "ReservationLedger":
        st = validate_budget_state(current)
        raw = st.get("reservations", {})
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise StateStoreError("stored reservations must be an object")
        reservations = {str(key): _validate_reservation(value) for key, value in raw.items()}
        return cls(
            max_tokens=max_tokens,
            max_calls=max_calls,
            max_cost_usd=max_cost_usd,
            period_bucket=period_bucket,
            tokens_used=int(st.get("tokens_used", 0)),
            calls_used=int(st.get("calls_used", 0)),
            cost_used=float(st.get("cost_used", 0.0)),
            reservations=reservations,
        )

    def to_store_state(self) -> Dict[str, Any]:
        return {
            "tokens_used": self.tokens_used,
            "calls_used": self.calls_used,
            "cost_used": self.cost_used,
            "reservations": {key: dict(value) for key, value in self.reservations.items()},
        }

    def held(self) -> Dict[str, float]:
        calls = 0
        tokens = 0.0
        cost = 0.0
        unbounded_tokens = False
        unbounded_cost = False
        for rec in self.reservations.values():
            if rec["status"] not in HOLD_STATUSES:
                continue
            calls += int(rec["calls"])
            if rec.get("tokens_bound") is None:
                unbounded_tokens = True
            else:
                tokens += float(rec["tokens_bound"])
            if rec.get("cost_bound") is None:
                unbounded_cost = True
            else:
                cost += float(rec["cost_bound"])
        return {
            "calls": calls,
            "tokens": tokens,
            "cost": cost,
            "unbounded_tokens": unbounded_tokens,
            "unbounded_cost": unbounded_cost,
        }

    def remaining(self) -> Dict[str, Optional[float]]:
        held = self.held()
        calls = None if self.max_calls is None else self.max_calls - self.calls_used - held["calls"]
        tokens = None if self.max_tokens is None else self.max_tokens - self.tokens_used - held["tokens"]
        cost = None if self.max_cost_usd is None else self.max_cost_usd - self.cost_used - held["cost"]
        return {"calls": calls, "tokens": tokens, "cost": cost}

    def reserve(
        self,
        reservation_id: str,
        *,
        calls: int = 1,
        tokens_bound: Optional[int] = None,
        cost_bound: Optional[float] = None,
        price_table_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not reservation_id or not isinstance(reservation_id, str):
            raise ReservationContractError("reservation_id is required")
        calls = int(_require_number("calls", calls))
        if calls < 1:
            raise ReservationContractError("calls must be at least 1")
        tokens_bound = _require_number("tokens_bound", tokens_bound, allow_none=True)
        cost_bound = _require_number("cost_bound", cost_bound, allow_none=True)
        if self.max_cost_usd is not None and cost_bound is None:
            raise MissingBound(
                "Cannot claim a dollar stop without a request-cost bound"
            )
        if self.max_tokens is not None and tokens_bound is None:
            raise MissingBound(
                "Cannot claim a token stop without a request-token bound"
            )
        existing = self.reservations.get(reservation_id)
        if existing is not None:
            if existing["status"] != STATUS_RESERVED:
                raise ReservationContractError(
                    f"reservation {reservation_id} is {existing['status']}"
                )
            if (
                existing["calls"] == calls
                and existing.get("tokens_bound") == tokens_bound
                and existing.get("cost_bound") == cost_bound
            ):
                return existing
            raise ReservationContractError(
                f"reservation {reservation_id} already exists with different bounds"
            )
        remaining = self.remaining()
        if remaining["calls"] is not None and calls > remaining["calls"]:
            raise BudgetExceeded(
                f"Call budget exhausted: held+settled would exceed {self.max_calls}; "
                "request not sent"
            )
        if remaining["tokens"] is not None and tokens_bound is not None:
            if tokens_bound > remaining["tokens"]:
                raise BudgetExceeded(
                    f"Token budget exhausted: held+settled would exceed {self.max_tokens}; "
                    "request not sent"
                )
        if remaining["cost"] is not None and cost_bound is not None:
            if cost_bound > remaining["cost"]:
                raise BudgetExceeded(
                    f"Cost budget exhausted: held+settled would exceed {self.max_cost_usd}; "
                    "request not sent"
                )
        rec = {
            "status": STATUS_RESERVED,
            "calls": calls,
            "tokens_bound": tokens_bound,
            "cost_bound": cost_bound,
            "price_table_version": price_table_version,
            "period_bucket": self.period_bucket,
            "tokens_settled": None,
            "cost_settled": None,
            "calls_settled": None,
        }
        self.reservations[reservation_id] = rec
        return rec

    def commit(
        self,
        reservation_id: str,
        *,
        calls: Optional[int] = None,
        tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        rec = self._require(reservation_id)
        tokens = int(_require_number("tokens", tokens))
        cost_usd = float(_require_number("cost_usd", cost_usd))
        settled_calls = int(rec["calls"] if calls is None else _require_number("calls", calls))
        if rec["status"] == STATUS_COMMITTED:
            if (
                rec.get("calls_settled") == settled_calls
                and rec.get("tokens_settled") == tokens
                and rec.get("cost_settled") == cost_usd
            ):
                return rec
            raise ReservationContractError(
                f"reservation {reservation_id} already committed with different usage"
            )
        if rec["status"] == STATUS_CANCELLED:
            raise ReservationContractError(
                f"reservation {reservation_id} is cancelled; cannot commit"
            )
        if rec["status"] not in HOLD_STATUSES:
            raise ReservationContractError(
                f"reservation {reservation_id} cannot commit from {rec['status']}"
            )
        rec["status"] = STATUS_COMMITTED
        rec["calls_settled"] = settled_calls
        rec["tokens_settled"] = tokens
        rec["cost_settled"] = cost_usd
        rec["estimate_overrun"] = bool(
            (rec.get("tokens_bound") is not None and tokens > rec["tokens_bound"])
            or (rec.get("cost_bound") is not None and cost_usd > rec["cost_bound"])
        )
        self.calls_used += settled_calls
        self.tokens_used += tokens
        self.cost_used += cost_usd
        return rec

    def cancel(
        self,
        reservation_id: str,
        *,
        dispatch_never_sent: bool = False,
        operator_attests_never_dispatched: bool = False,
    ) -> Dict[str, Any]:
        rec = self._require(reservation_id)
        if rec["status"] == STATUS_CANCELLED:
            return rec
        if rec["status"] == STATUS_COMMITTED:
            raise ReservationContractError(
                f"reservation {reservation_id} is committed; cannot cancel"
            )
        if rec["status"] == STATUS_RESERVED:
            if not dispatch_never_sent:
                raise ReservationContractError(
                    "Unknown provider outcome cannot silently free funds; "
                    "set dispatch_never_sent=True only when the request was not sent"
                )
            rec["status"] = STATUS_CANCELLED
            return rec
        if rec["status"] == STATUS_UNRESOLVED:
            if not operator_attests_never_dispatched:
                raise ReservationContractError(
                    "Unknown provider outcome cannot silently free funds; "
                    "operator must attest the request was never dispatched"
                )
            rec["status"] = STATUS_CANCELLED
            return rec
        raise ReservationContractError(
            f"reservation {reservation_id} cannot cancel from {rec['status']}"
        )

    def mark_unresolved(self, reservation_id: str, *, reason: str) -> Dict[str, Any]:
        rec = self._require(reservation_id)
        if rec["status"] == STATUS_UNRESOLVED:
            rec["unresolved_reason"] = reason
            return rec
        if rec["status"] != STATUS_RESERVED:
            raise ReservationContractError(
                f"reservation {reservation_id} cannot mark unresolved from {rec['status']}"
            )
        rec["status"] = STATUS_UNRESOLVED
        rec["unresolved_reason"] = reason
        return rec

    def recover_crash(self, reservation_id: str) -> Dict[str, Any]:
        """Process death cannot prove the request was unsent. Hold the funds."""
        return self.mark_unresolved(reservation_id, reason="process_death")

    def _require(self, reservation_id: str) -> Dict[str, Any]:
        rec = self.reservations.get(reservation_id)
        if rec is None:
            raise ReservationContractError(f"unknown reservation {reservation_id}")
        return rec
