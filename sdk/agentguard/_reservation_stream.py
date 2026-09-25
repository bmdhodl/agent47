"""Store-backed reservation for streamed provider patches (AG-05).

Private. No public export. In-memory guards keep ``check()`` then
``consume()`` after the stream. A ``StateStore`` holds capacity before the
provider call and settles once, when the stream finishes.

One ``create()`` or ``messages.stream()`` entry is one reservation. A later
application call is a second reservation. Retries inside that one provider
call stay on the same hold.

Missing usage under a token or dollar cap stays unresolved. It is not
recorded as an authoritative zero. A stream that stops before it finishes
keeps that hold too, including after a partial usage chunk. A calls-only
cap with no exception settles one call and zero tokens, because that cap
is a count, not a price. Unknown model cost uses ``resolve_billable_cost``
and is an overestimate, not a free call.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from ._reservation_path import _best_effort, _openai_bounds, _still_holding


def begin_stream_reservation(guard: Any, kwargs: dict) -> str:
    """Hold one stream before the provider function runs."""
    reservation_id = str(uuid.uuid4())
    guard.reserve_for_dispatch(reservation_id, **_openai_bounds(guard, kwargs))
    return reservation_id


def note_not_sent(ctx: Any, exc: BaseException, model: str) -> None:
    """Record that reserve refused the send. The provider was not called."""
    from ._reservation_contract import MissingBound
    from .guards import BudgetExceeded

    if not isinstance(exc, (BudgetExceeded, MissingBound)):
        return
    ctx.event(
        "guard.budget_exceeded",
        data={"message": str(exc), "model": model, "request_sent": False},
    )


def cancel_unsent_stream_reservation(guard: Any, reservation_id: str) -> None:
    """Release a hold only when this process has not called the provider."""
    _best_effort(
        lambda: guard.cancel_reservation(
            reservation_id, dispatch_never_sent=True
        )
    )


def dispatch_failure_reason(exc: BaseException) -> str:
    """Timeout after the call starts is not proof the request never left."""
    if type(exc).__name__ in {"TimeoutError", "TimeoutExceeded"}:
        return "timeout"
    return "provider_outcome_unknown"


def abandon_stream_reservation(guard: Any, reservation_id: str, *, reason: str) -> None:
    """Keep the hold when the provider outcome is unknown."""
    _best_effort(
        lambda: guard.mark_reservation_unresolved(reservation_id, reason=reason)
    )


def settle_stream_reservation(
    guard: Any,
    ctx: Any,
    reservation_id: str,
    model: str,
    provider: str,
    usage: Any,
    response: Any,
    *,
    prices: Optional[dict] = None,
    completed: bool = True,
    error: Optional[BaseException] = None,
) -> None:
    """Commit final usage once, or keep the hold when the outcome is not billable.

    ``prices`` overrides the owned table for this settlement only. Patched
    streams omit it and use ``DEFAULT_PRICE_TABLE``. This is not a new
    ``BudgetGuard`` argument.

    ``completed`` is true only when the stream ran to the end or returned a
    final message. An exception, or a close after a partial chunk, does not
    release a token or dollar hold.
    """
    if usage is None and response is not None:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
    reason = _incomplete_reason(guard, usage, completed=completed, error=error)
    if reason is not None:
        guard.mark_reservation_unresolved(reservation_id, reason=reason)
        ctx.event(
            "llm.result",
            data={
                "model": model,
                "provider": provider,
                "usage": None,
                "stream": True,
                "source_of_cost": "unresolved",
                "reason": reason,
                "reservation_id": reservation_id,
            },
        )
        return
    if usage is None:
        _settle_missing(guard, ctx, reservation_id, model, provider)
        return
    _settle_present(
        guard, ctx, reservation_id, model, provider, usage, prices=prices
    )


def _incomplete_reason(
    guard: Any,
    usage: Any,
    *,
    completed: bool,
    error: Optional[BaseException],
) -> Optional[str]:
    """Return an unresolved reason when settling would shrink a real hold."""
    if error is not None:
        return dispatch_failure_reason(error)
    if completed:
        return None
    if guard.max_tokens is None and guard.max_cost_usd is None:
        return None
    if usage is None:
        return "usage_missing"
    return "stream_incomplete"


def _settle_missing(
    guard: Any, ctx: Any, reservation_id: str, model: str, provider: str
) -> None:
    if guard.max_tokens is not None or guard.max_cost_usd is not None:
        guard.mark_reservation_unresolved(reservation_id, reason="usage_missing")
        ctx.event(
            "llm.result",
            data={
                "model": model,
                "provider": provider,
                "usage": None,
                "stream": True,
                "source_of_cost": "unresolved",
                "reason": "usage_missing",
                "reservation_id": reservation_id,
            },
        )
        return
    guard.commit_reservation(reservation_id, tokens=0, cost_usd=0.0, calls=1)
    ctx.event(
        "llm.result",
        data={
            "model": model,
            "provider": provider,
            "usage": None,
            "stream": True,
            "source_of_cost": "missing",
            "reservation_id": reservation_id,
        },
    )


def _settle_present(
    guard: Any,
    ctx: Any,
    reservation_id: str,
    model: str,
    provider: str,
    usage: Any,
    *,
    prices: Optional[dict],
) -> None:
    from .precision_cost import (
        SOURCE_ZERO,
        CostResolutionError,
        resolve_billable_cost,
    )

    try:
        resolved = resolve_billable_cost(
            {"usage": usage},
            model=model,
            provider=provider,
            prices=prices,
            strict=False,
        )
    except CostResolutionError:
        if _still_holding(guard, reservation_id):
            abandon_stream_reservation(
                guard, reservation_id, reason="cost_unresolved"
            )
        raise
    except Exception:
        if _still_holding(guard, reservation_id):
            abandon_stream_reservation(
                guard, reservation_id, reason="settlement_failed"
            )
        raise

    source = str(resolved.get("source") or "")
    cost = float(resolved.get("cost_usd") or 0.0)
    if cost == 0.0 and source != SOURCE_ZERO:
        if _still_holding(guard, reservation_id):
            guard.mark_reservation_unresolved(
                reservation_id, reason="cost_unresolved"
            )
        ctx.event(
            "llm.result",
            data={
                "model": model,
                "provider": provider,
                "usage": usage if isinstance(usage, dict) else None,
                "stream": True,
                "source_of_cost": "unresolved",
                "reason": "cost_unresolved",
                "reservation_id": reservation_id,
            },
        )
        return

    token_map = resolved.get("tokens") or {}
    total = int(token_map.get("total") or 0)
    try:
        record = guard.commit_reservation(
            reservation_id, tokens=total, cost_usd=cost, calls=1
        )
    except Exception:
        if _still_holding(guard, reservation_id):
            abandon_stream_reservation(
                guard, reservation_id, reason="settlement_failed"
            )
        raise
    breakdown = resolved.get("breakdown") or {}
    ctx.event(
        "llm.result",
        data={
            "model": model,
            "provider": provider,
            "usage": {"total_tokens": total},
            "stream": True,
            "source_of_cost": source,
            "price_table_version": breakdown.get("price_table_version"),
            "estimate_overrun": bool(record.get("estimate_overrun")),
            "reservation_id": reservation_id,
        },
        cost_usd=cost if cost > 0 else None,
    )
