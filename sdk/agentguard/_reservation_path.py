"""Store-backed reservation for one OpenAI dispatch path (AG-04).

``BudgetGuard.check()`` and ``consume()`` stay recorded-budget preflight.
Sync, non-streaming OpenAI Chat Completions calls that use a ``StateStore``
reserve before send, commit provider usage, and cancel only when this process
still has not called the provider. Timeout, crash, and unknown provider
outcome keep the hold.

Lock order matches ``_consume_persistent``: ``BudgetGuard._lock``, then one
``StateStore.update``. Each transition is one critical section. There is no
retry loop here.

This is not a public type and not an invoice cap. ``ReservationLedger`` stays
private. The methods bound onto ``BudgetGuard`` are the read and transition
surface for this path.
"""
from __future__ import annotations

import sys
import uuid
from typing import Any, Callable, Dict, Optional

from ._reservation_contract import MissingBound, ReservationLedger
from .price_table import _DEFAULT_HIGH_WATER_PER_TOKEN, DEFAULT_PRICE_TABLE

_RESERVED = "reserved"
_UNRESOLVED = "unresolved"


def bind_budget_guard(cls: type) -> None:
    """Attach reservation methods without growing ``guards.py`` past the line cap."""
    cls.reserve_for_dispatch = reserve_for_dispatch
    cls.commit_reservation = commit_reservation
    cls.cancel_reservation = cancel_reservation
    cls.mark_reservation_unresolved = mark_reservation_unresolved
    cls.recover_reservation = recover_reservation
    cls.reservation_totals = reservation_totals


def reserve_for_dispatch(
    self: Any,
    reservation_id: str,
    *,
    calls: int = 1,
    tokens_bound: Optional[int] = None,
    cost_bound: Optional[float] = None,
    price_table_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Hold capacity before a provider send. Raises if the store cannot fit the hold."""
    holder = _mutate(
        self,
        lambda ledger: ledger.reserve(
            reservation_id,
            calls=calls,
            tokens_bound=tokens_bound,
            cost_bound=cost_bound,
            price_table_version=price_table_version,
        ),
    )
    return holder["record"]


def commit_reservation(
    self: Any,
    reservation_id: str,
    *,
    tokens: int = 0,
    calls: Optional[int] = None,
    cost_usd: float = 0.0,
) -> Dict[str, Any]:
    """Settle a hold with provider usage. Same usage twice is a no-op.

    Usage is stored before any limit exception is raised. ``BudgetExceeded``
    means the provider usage was recorded, not blocked.

    The check uses the totals from this store write and runs before this
    guard's lock is released, same as ``consume()``. A later ``consume()``
    checks its own write.
    """
    from .guards import BudgetExceeded

    def _enforce(holder: Dict[str, Any]) -> None:
        if not holder["increased"]:
            return
        try:
            self._enforce_limits(
                holder["state"]["tokens_used"],
                holder["state"]["calls_used"],
                holder["state"]["cost_used"],
                tokens,
                holder["added_calls"],
                cost_usd,
            )
        except BudgetExceeded as exc:
            holder["limit_error"] = exc
        else:
            if self._warn_at_pct is not None and not self._warned:
                holder["warning"] = self._check_warning()

    holder = _mutate(
        self,
        lambda ledger: ledger.commit(
            reservation_id, calls=calls, tokens=tokens, cost_usd=cost_usd
        ),
        after=_enforce,
    )
    if not holder["increased"]:
        return holder["record"]
    error: Optional[BaseException] = holder.get("limit_error")
    warning = holder.get("warning")
    from .goal import _enforce_active_goal_limits, _record_consume

    added_calls = holder["added_calls"]
    _record_consume(tokens=int(tokens), calls=int(added_calls), cost_usd=float(cost_usd))
    try:
        _enforce_active_goal_limits(tokens, added_calls, cost_usd)
    except BudgetExceeded:
        if error is None:
            raise
    if warning is not None and self._on_warning is not None:
        self._on_warning(warning)
    if error is not None:
        raise error
    return holder["record"]


def cancel_reservation(
    self: Any,
    reservation_id: str,
    *,
    dispatch_never_sent: bool = False,
    operator_attests_never_dispatched: bool = False,
) -> Dict[str, Any]:
    """Release a hold only with evidence the request never left this process."""
    holder = _mutate(
        self,
        lambda ledger: ledger.cancel(
            reservation_id,
            dispatch_never_sent=dispatch_never_sent,
            operator_attests_never_dispatched=operator_attests_never_dispatched,
        ),
    )
    return holder["record"]


def mark_reservation_unresolved(
    self: Any, reservation_id: str, *, reason: str
) -> Dict[str, Any]:
    """Keep the hold when the provider outcome is unknown."""
    holder = _mutate(
        self, lambda ledger: ledger.mark_unresolved(reservation_id, reason=reason)
    )
    return holder["record"]


def recover_reservation(self: Any, reservation_id: str) -> Dict[str, Any]:
    """Process death cannot prove the request was unsent. Keep the hold."""
    holder = _mutate(self, lambda ledger: ledger.recover_crash(reservation_id))
    return holder["record"]


def reservation_totals(self: Any) -> Dict[str, Any]:
    """Settled counters plus reserved and unresolved holds.

    In-memory guards have no holds. A store read uses the same lock order as
    consume: this guard's lock, then the store.
    """
    if self._store is None:
        with self._lock:
            return _totals_from_counters(
                {
                    "tokens_used": self.state.tokens_used,
                    "calls_used": self.state.calls_used,
                    "cost_used": self.state.cost_used,
                }
            )
    bucket = self._period_bucket()
    with self._lock:
        current = self._store.read(bucket)
    if current is None:
        return _totals_from_counters({})
    ledger = ReservationLedger.from_store_state(
        current,
        max_tokens=self._max_tokens,
        max_calls=self._max_calls,
        max_cost_usd=self._max_cost_usd,
        period_bucket=bucket,
    )
    return _totals_from_ledger(ledger)


def traced_openai_reserved(
    original: Callable[..., Any],
    tracer: Any,
    budget_guard: Any,
    args: tuple,
    kwargs: Dict[str, Any],
    *,
    before_send: Optional[Callable[[], None]] = None,
) -> Any:
    """Reserve, send once, then commit. Cancel only if ``before_send`` aborts."""
    from .guards import BudgetExceeded

    model = str(kwargs.get("model", "unknown"))
    span_cm = tracer.trace(
        f"llm.openai.{model}",
        data={"model": model, "provider": "openai"},
    )
    ctx = span_cm.__enter__()
    reservation_id = str(uuid.uuid4())
    try:
        bounds = _openai_bounds(budget_guard, kwargs)
        budget_guard.reserve_for_dispatch(reservation_id, **bounds)
    except BaseException as exc:
        if isinstance(exc, (BudgetExceeded, MissingBound)):
            ctx.event(
                "guard.budget_exceeded",
                data={"message": str(exc), "model": model, "request_sent": False},
            )
        span_cm.__exit__(*sys.exc_info())
        raise
    try:
        if before_send is not None:
            before_send()
    except BaseException:
        _best_effort(
            lambda: budget_guard.cancel_reservation(
                reservation_id, dispatch_never_sent=True
            )
        )
        span_cm.__exit__(*sys.exc_info())
        raise
    try:
        result = original(*args, **kwargs)
    except BaseException:
        _best_effort(
            lambda: budget_guard.mark_reservation_unresolved(
                reservation_id, reason="provider_outcome_unknown"
            )
        )
        span_cm.__exit__(*sys.exc_info())
        raise
    try:
        _commit_provider_result(budget_guard, ctx, reservation_id, model, result)
    except BaseException:
        if _still_holding(budget_guard, reservation_id):
            _best_effort(
                lambda: budget_guard.mark_reservation_unresolved(
                    reservation_id, reason="settlement_failed"
                )
            )
        span_cm.__exit__(*sys.exc_info())
        raise
    span_cm.__exit__(None, None, None)
    return result


def _openai_bounds(guard: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    token_cap = kwargs.get("max_completion_tokens", kwargs.get("max_tokens"))
    tokens_bound = _positive_int_bound(token_cap)
    cost_bound = None
    version = None
    if guard.max_cost_usd is not None:
        if tokens_bound is None:
            raise MissingBound(
                "Cannot claim a dollar stop without max_tokens on the request"
            )
        over = DEFAULT_PRICE_TABLE.get("overestimate") or {}
        per_token = float(over.get("high_water_per_token", _DEFAULT_HIGH_WATER_PER_TOKEN))
        cost_bound = tokens_bound * per_token
        version = str(DEFAULT_PRICE_TABLE.get("version") or "")
    held_tokens = tokens_bound if guard.max_tokens is not None else None
    # A dollar cap already refused a missing token bound above. This covers
    # a token cap on its own.
    if guard.max_tokens is not None and held_tokens is None:
        raise MissingBound(
            "Cannot claim a token stop without max_tokens on the request"
        )
    return {
        "calls": 1,
        "tokens_bound": held_tokens,
        "cost_bound": cost_bound,
        "price_table_version": version,
    }


def _positive_int_bound(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MissingBound("max_tokens must be a positive integer to reserve a bound")
    return value


def _commit_provider_result(
    guard: Any, ctx: Any, reservation_id: str, model: str, result: Any
) -> None:
    from .precision_cost import resolve_billable_cost

    usage = getattr(result, "usage", None)
    if usage is None and isinstance(result, dict):
        usage = result.get("usage")
    if usage is None:
        guard.commit_reservation(reservation_id, tokens=0, cost_usd=0.0, calls=1)
        ctx.event(
            "llm.result",
            data={
                "model": model,
                "provider": "openai",
                "usage": None,
                "source_of_cost": "missing",
            },
        )
        return
    resolved = resolve_billable_cost(result, model=model, provider="openai", strict=False)
    token_map = resolved.get("tokens") or {}
    total = int(token_map.get("total") or 0)
    cost = float(resolved.get("cost_usd") or 0.0)
    record = guard.commit_reservation(
        reservation_id, tokens=total, cost_usd=cost, calls=1
    )
    ctx.event(
        "llm.result",
        data={
            "model": model,
            "provider": "openai",
            "usage": {"total_tokens": total},
            "source_of_cost": str(resolved.get("source", "estimate")),
            "estimate_overrun": bool(record.get("estimate_overrun")),
            "reservation_id": reservation_id,
        },
        cost_usd=cost if cost > 0 else None,
    )


def _mutate(
    guard: Any,
    operation: Callable[[ReservationLedger], Dict[str, Any]],
    after: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Apply one ledger transition under the guard lock, then the store lock.

    ``after`` runs before the guard lock is released, on the state this write
    stored. ``guards`` is imported here so loading this module does not import
    ``guards`` while ``BudgetGuard`` is still being defined.
    """
    from .guards import BudgetState

    if guard._store is None:
        raise ValueError("reservation requires a StateStore")
    bucket = guard._period_bucket()
    holder: Dict[str, Any] = {}

    def mutator(current: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        ledger = ReservationLedger.from_store_state(
            current,
            max_tokens=guard._max_tokens,
            max_calls=guard._max_calls,
            max_cost_usd=guard._max_cost_usd,
            period_bucket=bucket,
        )
        before_calls = ledger.calls_used
        before_tokens = ledger.tokens_used
        before_cost = ledger.cost_used
        holder["record"] = operation(ledger)
        holder["added_calls"] = ledger.calls_used - before_calls
        holder["added_tokens"] = ledger.tokens_used - before_tokens
        holder["added_cost"] = ledger.cost_used - before_cost
        holder["increased"] = holder["added_calls"] or holder["added_tokens"] or holder["added_cost"]
        return ledger.to_store_state()

    with guard._lock:
        new = guard._store.update(bucket, mutator)
        guard.state = BudgetState(
            tokens_used=int(new.get("tokens_used", 0)),
            calls_used=int(new.get("calls_used", 0)),
            cost_used=float(new.get("cost_used", 0.0)),
        )
        holder["state"] = new
        if after is not None:
            after(holder)
    return holder


def _totals_from_counters(current: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "settled": {
            "calls": int(current.get("calls_used", 0) or 0),
            "tokens": int(current.get("tokens_used", 0) or 0),
            "cost": float(current.get("cost_used", 0.0) or 0.0),
        },
        "reserved": {"calls": 0, "tokens": 0.0, "cost": 0.0},
        "unresolved": {"calls": 0, "tokens": 0.0, "cost": 0.0},
        "reservation_ids": {"reserved": [], "unresolved": []},
    }


def _totals_from_ledger(ledger: ReservationLedger) -> Dict[str, Any]:
    buckets = {
        _RESERVED: {"calls": 0, "tokens": 0.0, "cost": 0.0},
        _UNRESOLVED: {"calls": 0, "tokens": 0.0, "cost": 0.0},
    }
    ids: Dict[str, list] = {_RESERVED: [], _UNRESOLVED: []}
    for reservation_id, record in ledger.reservations.items():
        status = record.get("status")
        if status not in buckets:
            continue
        ids[status].append(reservation_id)
        buckets[status]["calls"] += int(record.get("calls") or 0)
        if record.get("tokens_bound") is not None:
            buckets[status]["tokens"] += float(record["tokens_bound"])
        if record.get("cost_bound") is not None:
            buckets[status]["cost"] += float(record["cost_bound"])
    return {
        "settled": {
            "calls": ledger.calls_used,
            "tokens": ledger.tokens_used,
            "cost": ledger.cost_used,
        },
        "reserved": buckets[_RESERVED],
        "unresolved": buckets[_UNRESOLVED],
        "reservation_ids": {
            "reserved": sorted(ids[_RESERVED]),
            "unresolved": sorted(ids[_UNRESOLVED]),
        },
    }


def _still_holding(guard: Any, reservation_id: str) -> bool:
    """See if a hold is still reserved before a best-effort unresolved mark.

    The read and the later mark take the guard lock separately. A cancel in
    between frees the hold. The later mark then fails and is swallowed.
    """
    try:
        totals = guard.reservation_totals()
    except Exception:
        return False
    ids = totals.get("reservation_ids") or {}
    return reservation_id in ids.get("reserved", ())


def _best_effort(action: Callable[[], None]) -> None:
    try:
        action()
    except Exception:
        return
