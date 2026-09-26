"""Budget checks and llm.result billing shared by the provider patches."""
from __future__ import annotations

from typing import Any, Dict

from agentguard.usage import normalize_usage


def _check_budget_before_request(budget_guard: Any, ctx: Any, model: str) -> None:
    """Reject exhausted budgets before crossing the provider boundary."""
    from agentguard.guards import BudgetExceeded

    if budget_guard is None:
        return
    try:
        budget_guard.check()
    except BudgetExceeded as exc:
        ctx.event("guard.budget_exceeded", data={
            "message": str(exc), "model": model, "request_sent": False,
        })
        raise


def _consume_budget(
    budget_guard: Any,
    ctx: Any,
    tokens: int,
    calls: int,
    cost_usd: float,
    model: str,
) -> None:
    """Feed consumption into BudgetGuard, emitting trace events for warnings/exceeded."""
    from agentguard.guards import BudgetExceeded

    was_warned = getattr(budget_guard, "_warned", False)
    try:
        budget_guard.consume(tokens=tokens, calls=calls, cost_usd=cost_usd)
    except BudgetExceeded as exc:
        ctx.event("guard.budget_exceeded", data={
            "message": str(exc),
            "model": model,
            "cost_usd": cost_usd,
            "tokens": tokens,
        })
        raise
    if not was_warned and getattr(budget_guard, "_warned", False):
        state = getattr(budget_guard, "state", None)
        ctx.event("guard.budget_warning", data={
            "model": model,
            "tokens_used": getattr(state, "tokens_used", 0) if state else 0,
            "calls_used": getattr(state, "calls_used", 0) if state else 0,
            "cost_used": getattr(state, "cost_used", 0.0) if state else 0.0,
        })


def _emit_llm_result(
    ctx: Any,
    budget_guard: Any,
    model: str,
    provider: str,
    usage: Any,
    response: Any = None,
) -> None:
    """Extract usage from an LLM response and emit llm.result event + budget consume.

    Shared by all 4 patch variants (OpenAI sync/async, Anthropic sync/async).

    Cost uses ``resolve_billable_cost`` (provider fields → owned table → estimate
    → overestimate). Call once per provider hit with the *final* usage/response
    so streaming chunks are not double-counted. Do not also call
    ``consume_billable`` for the same event — that would double-consume.
    """
    from agentguard.precision_cost import (
        CostResolutionError,
        log_consume_event,
        resolve_billable_cost,
    )

    # Prefer full response when available so provider cost fields are visible.
    billable_payload = response if response is not None else usage
    usage_data = normalize_usage(usage, provider=provider)
    if usage_data is None and billable_payload is None:
        return

    try:
        # strict=False still honors STRICT_PRECISION=1 via resolve_billable_cost.
        resolved = resolve_billable_cost(
            billable_payload if billable_payload is not None else {"usage": usage_data},
            model=model,
            provider=provider,
            strict=False,
        )
    except CostResolutionError:
        # Fail-loud under STRICT_PRECISION: never silently under-count as $0.
        raise
    except Exception:
        # Unexpected resolver bugs must not under-count. Prefer a conservative
        # overestimate (via non-strict re-resolve on usage-only) over $0.
        if usage_data is None:
            raise
        try:
            resolved = resolve_billable_cost(
                {"usage": usage_data},
                model=model,
                provider=provider,
                strict=False,
            )
        except CostResolutionError:
            raise
        except Exception:
            # Last resort: force overestimate source with high-water charge.
            from agentguard.precision_cost import (
                DEFAULT_PRICE_TABLE,
                SOURCE_OVERESTIMATE,
                _overestimate_cost,
                extract_tokens,
            )

            tokens_fb = extract_tokens(
                {"usage": usage_data}, provider=provider
            )
            over = _overestimate_cost(tokens_fb, DEFAULT_PRICE_TABLE)
            resolved = {
                "cost_usd": float(over),
                "tokens": tokens_fb,
                "source": SOURCE_OVERESTIMATE,
                "breakdown": {"reason": "resolver_exception_overestimate"},
            }

    tokens = resolved.get("tokens") or {}
    total_tokens = int(tokens.get("total", 0) or (usage_data or {}).get("total_tokens", 0) or 0)
    cost = float(resolved.get("cost_usd", 0.0) or 0.0)
    source = str(resolved.get("source", "estimate"))
    request_id = resolved.get("request_id")

    log_consume_event(
        model=model,
        provider=provider,
        tokens=tokens if tokens else {
            "input": (usage_data or {}).get("input_tokens", 0),
            "output": (usage_data or {}).get("output_tokens", 0),
            "cached": (usage_data or {}).get("cached_input_tokens", 0),
            "total": total_tokens,
        },
        cost_usd=cost,
        source_of_cost=source,
        request_id=request_id if isinstance(request_id, str) else None,
    )

    event_data: Dict[str, Any] = {
        "model": model,
        "provider": provider,
        "usage": usage_data,
        "source_of_cost": source,
    }
    if request_id:
        event_data["request_id"] = request_id
    ctx.event(
        "llm.result",
        data=event_data,
        cost_usd=cost if cost > 0 else None,
    )
    if budget_guard is not None:
        _consume_budget(budget_guard, ctx, total_tokens, 1, cost, model)


def _emit_stream_final(
    ctx: Any,
    budget_guard: Any,
    model: str,
    provider: str,
    usage: Any,
    response: Any,
) -> None:
    from agentguard.instrument_stream import emit_stream_final

    emit_stream_final(
        ctx,
        budget_guard,
        model,
        provider,
        usage,
        response,
        _emit_llm_result,
        _consume_budget,
    )
