"""LangGraph integration — guard-aware node wrappers for StateGraph.

Wraps LangGraph node functions with AgentGuard tracing and runtime guards.
Each node execution becomes a span; guards fire at node boundaries.

Usage::

    from agentguard.integrations.langgraph import guarded_node
    from agentguard import Tracer, LoopGuard, BudgetGuard

    tracer = Tracer(sink=JsonlFileSink("traces.jsonl"))

    @guarded_node(
        tracer=tracer,
        loop_guard=LoopGuard(max_repeats=3),
        budget_guard=BudgetGuard(max_cost_usd=5.00),
    )
    def research_node(state):
        # your node logic
        return {"messages": state["messages"] + [result]}

    # Or wrap at graph construction time:
    builder.add_node("research", guard_node(research_fn, tracer=tracer))

Requires ``langgraph`` (optional dependency). Core SDK remains zero-dep.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, TypeVar

from agentguard.guards import (
    BudgetGuard,
    BudgetExceeded,
    LoopGuard,
    LoopDetected,
)
from agentguard.tracing import Tracer

F = TypeVar("F", bound=Callable[..., Any])


def guarded_node(
    tracer: Optional[Tracer] = None,
    loop_guard: Optional[LoopGuard] = None,
    budget_guard: Optional[BudgetGuard] = None,
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator that wraps a LangGraph node function with tracing and guards.

    Args:
        tracer: AgentGuard Tracer instance. Creates a default if None.
        loop_guard: Optional LoopGuard — detects repeated node invocations.
        budget_guard: Optional BudgetGuard — enforces token/call/cost limits.
        name: Span name override. Defaults to ``node.<function_name>``.

    Returns:
        Decorated function with same signature.

    Raises:
        LoopDetected: If the loop guard detects repeated identical calls.
        BudgetExceeded: If the budget guard limit is hit.
    """
    _tracer = tracer or Tracer()

    def decorator(fn: F) -> F:
        node_name = name or f"node.{fn.__name__}"

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract state for guard context
            state = args[0] if args else kwargs.get("state", {})
            state_summary = _summarize_state(state)

            # Check loop guard before execution
            if loop_guard:
                loop_guard.check(
                    tool_name=node_name,
                    tool_args=state_summary,
                )

            # Check budget guard before execution
            if budget_guard:
                budget_guard.consume(calls=1)

            # Execute node inside a traced span
            with _tracer.trace(node_name, data=state_summary) as ctx:
                try:
                    result = fn(*args, **kwargs)
                    ctx.event(
                        f"{node_name}.result",
                        data=_summarize_state(result) if result else {},
                    )
                    return result
                except (LoopDetected, BudgetExceeded):
                    raise
                except Exception:
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator


def guard_node(
    fn: Callable[..., Any],
    tracer: Optional[Tracer] = None,
    loop_guard: Optional[LoopGuard] = None,
    budget_guard: Optional[BudgetGuard] = None,
    name: Optional[str] = None,
) -> Callable[..., Any]:
    """Wrap a node function for use with ``builder.add_node()``.

    Non-decorator form of :func:`guarded_node`::

        builder.add_node("research", guard_node(research_fn, tracer=tracer))

    Args:
        fn: The node function to wrap.
        tracer: AgentGuard Tracer instance.
        loop_guard: Optional LoopGuard.
        budget_guard: Optional BudgetGuard.
        name: Span name override. Defaults to ``node.<function_name>``.

    Returns:
        Wrapped function.
    """
    return guarded_node(
        tracer=tracer,
        loop_guard=loop_guard,
        budget_guard=budget_guard,
        name=name,
    )(fn)


def _summarize_state(state: Any) -> Dict[str, Any]:
    """Extract a safe summary dict from LangGraph state.

    Handles dict states (most common), dataclass-like objects, and fallbacks.
    Truncates large values to avoid bloating trace events.
    """
    if state is None:
        return {}
    if isinstance(state, dict):
        summary: Dict[str, Any] = {}
        for k, v in state.items():
            if k == "messages" and isinstance(v, list):
                summary["message_count"] = len(v)
                if v:
                    last = v[-1]
                    content = getattr(last, "content", str(last))
                    summary["last_message"] = str(content)[:200]
            else:
                s = repr(v)
                summary[k] = s[:200] if len(s) > 200 else v
        return summary
    return {"state": repr(state)[:500]}
