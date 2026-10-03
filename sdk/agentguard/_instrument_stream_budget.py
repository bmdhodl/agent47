"""Private accounting and reservation steps for provider streams."""
from __future__ import annotations

from typing import Any, Callable, Dict


def emit_stream_final(
    ctx: Any,
    budget_guard: Any,
    model: str,
    provider: str,
    usage: Any,
    response: Any,
    emit_result: Callable[..., None],
    consume_budget: Callable[..., None],
    *, free_local: bool = False,
) -> None:
    """Bill a completed stream once. Count the dispatched call if usage is missing."""
    resolved_usage = usage
    if resolved_usage is None and response is not None:
        resolved_usage = getattr(response, "usage", None)
    if resolved_usage is not None:
        emit_result(
            ctx,
            budget_guard,
            model,
            provider,
            resolved_usage,
            response={"usage": resolved_usage},
        )
        return
    ctx.event(
        "llm.result",
        data={"model": model, "provider": provider, "usage": None, "stream": True,
              **({"source_of_cost": "zero"} if free_local else {})},
        cost_usd=0.0 if free_local else None,
    )
    if budget_guard is not None:
        consume_budget(budget_guard, ctx, 0, 1, 0.0, model)


def _store_backed_stream(budget_guard: Any, wrap_stream: bool) -> bool:
    return bool(
        wrap_stream
        and budget_guard is not None
        and getattr(budget_guard, "_store", None) is not None
    )


def _prepare_stream_call(
    ctx: Any,
    budget_guard: Any,
    model: str,
    kwargs: Dict[str, Any],
    wrap_stream: bool,
    check_budget: Callable[..., None],
    *, free_local: bool = False,
) -> Any:
    """Reserve a stored stream, or preflight an in-memory budget."""
    if not _store_backed_stream(budget_guard, wrap_stream):
        check_budget(budget_guard, ctx, model)
        return None
    from ._reservation_stream import begin_stream_reservation, note_not_sent

    try:
        return begin_stream_reservation(budget_guard, kwargs, free_local=free_local)
    except BaseException as exc:
        note_not_sent(ctx, exc, model)
        raise


def _fail_stream_dispatch(budget_guard: Any, reservation_id: Any, exc: BaseException) -> None:
    if reservation_id is None:
        return
    from ._reservation_stream import abandon_stream_reservation, dispatch_failure_reason

    abandon_stream_reservation(
        budget_guard, reservation_id, reason=dispatch_failure_reason(exc)
    )


def _cancel_unsent_stream(budget_guard: Any, reservation_id: Any) -> None:
    if reservation_id is None:
        return
    from ._reservation_stream import cancel_unsent_stream_reservation

    cancel_unsent_stream_reservation(budget_guard, reservation_id)


def _finish_stream(
    ctx: Any,
    budget_guard: Any,
    model: str,
    provider: str,
    usage: Any,
    response: Any,
    reservation_id: Any,
    emit_result: Callable[..., None],
    consume_budget: Callable[..., None],
    *,
    completed: bool = True,
    error: Any = None,
    free_local: bool = False,
) -> None:
    if reservation_id is None:
        emit_stream_final(
            ctx, budget_guard, model, provider, usage, response,
            emit_result, consume_budget,
            free_local=free_local,
        )
        return
    from ._reservation_stream import settle_stream_reservation

    settle_stream_reservation(
        budget_guard,
        ctx,
        reservation_id,
        model,
        provider,
        usage,
        response,
        completed=completed,
        error=error,
        free_local=free_local,
    )


