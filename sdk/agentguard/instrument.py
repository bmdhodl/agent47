"""Auto-instrumentation decorators and monkey-patches."""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# Store originals for unpatch support
_originals: Dict[str, Any] = {}


def _consume_budget(
    budget_guard: Any,
    ctx: Any,
    tokens: int,
    calls: int,
    cost_usd: float,
    model: str,
) -> None:
    """Feed consumption into BudgetGuard, emitting trace events for warnings/exceeded.

    T5: Emits ``guard.budget_exceeded`` event before re-raising BudgetExceeded.
    T6: Emits ``guard.budget_warning`` event when warning threshold is crossed.
    """
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
    # Check if warning threshold was just crossed (T6)
    if not was_warned and getattr(budget_guard, "_warned", False):
        state = getattr(budget_guard, "state", None)
        ctx.event("guard.budget_warning", data={
            "model": model,
            "tokens_used": getattr(state, "tokens_used", 0) if state else 0,
            "calls_used": getattr(state, "calls_used", 0) if state else 0,
            "cost_used": getattr(state, "cost_used", 0.0) if state else 0.0,
        })


def trace_agent(tracer: Any, name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator that wraps a function in a top-level trace span.

    Usage::

        @trace_agent(tracer)
        def my_agent(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"agent.{fn.__name__}"

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.trace(span_name) as ctx:
                kwargs["_trace_ctx"] = ctx
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    raise
                finally:
                    kwargs.pop("_trace_ctx", None)

        # If the function doesn't accept **kwargs, fall back to simple wrapping
        @functools.wraps(fn)
        def simple_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.trace(span_name):
                return fn(*args, **kwargs)

        # Check if function can accept _trace_ctx kwarg
        import inspect

        sig = inspect.signature(fn)
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        has_trace_ctx = "_trace_ctx" in sig.parameters

        if has_var_keyword or has_trace_ctx:
            return wrapper  # type: ignore[return-value]
        return simple_wrapper  # type: ignore[return-value]

    return decorator


def trace_tool(tracer: Any, name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator that wraps a function in a tool span.

    Usage::

        @trace_tool(tracer)
        def search(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"tool.{fn.__name__}"

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.trace(span_name) as ctx:
                result = fn(*args, **kwargs)
                ctx.event("tool.result", data={"result": str(result)[:500]})
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


def patch_openai(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch OpenAI client to auto-trace chat completions.

    Works with openai >= 1.0 (instance-based client) and < 1.0 (module-based).
    Safe to call even if openai is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard. Each call's cost/tokens are
            fed into ``guard.consume()`` automatically.
    """
    try:
        import openai  # noqa: F811
    except ImportError:
        return

    # openai >= 1.0: chat/completions are instance attributes, not class attrs.
    # We wrap __init__ to patch each instance after construction.
    client_cls = getattr(openai, "OpenAI", None)
    if client_cls is not None:
        if "openai_init" in _originals:
            return  # already patched

        original_init = client_cls.__init__

        @functools.wraps(original_init)
        def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            _patch_openai_instance(self, tracer, budget_guard)

        _originals["openai_init"] = original_init
        _originals["openai_cls"] = client_cls
        client_cls.__init__ = patched_init  # type: ignore[attr-defined]
        return

    # openai < 1.0: module-level ChatCompletion
    chat = getattr(openai, "ChatCompletion", None)
    if chat is None:
        return
    _original = getattr(chat, "create", None)
    if _original is None:
        return

    _originals["openai_legacy_create"] = _original
    _originals["openai_legacy_chat"] = chat

    @functools.wraps(_original)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        return _traced_openai_create(_original, tracer, budget_guard, *args, **kwargs)

    chat.create = traced_create  # type: ignore[attr-defined]


def _patch_openai_instance(client: Any, tracer: Any, budget_guard: Any = None) -> None:
    """Patch a single OpenAI client instance's chat.completions.create."""
    chat = getattr(client, "chat", None)
    if chat is None:
        return
    completions = getattr(chat, "completions", None)
    if completions is None:
        return
    original_create = completions.create

    @functools.wraps(original_create)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        return _traced_openai_create(original_create, tracer, budget_guard, *args, **kwargs)

    completions.create = traced_create  # type: ignore[attr-defined]


def _traced_openai_create(
    original: Any, tracer: Any, budget_guard: Any, *args: Any, **kwargs: Any
) -> Any:
    """Shared traced wrapper for OpenAI create calls."""
    model = kwargs.get("model", "unknown")
    with tracer.trace(f"llm.openai.{model}") as ctx:
        result = original(*args, **kwargs)
        usage = getattr(result, "usage", None)
        if usage is not None:
            input_tokens = getattr(usage, "prompt_tokens", 0)
            output_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)
            from agentguard.cost import estimate_cost

            cost = estimate_cost(model, input_tokens, output_tokens, provider="openai")
            event_data: dict = {
                "model": model,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
            }
            ctx.event("llm.result", data=event_data, cost_usd=cost if cost > 0 else None)
            if budget_guard is not None:
                _consume_budget(budget_guard, ctx, total_tokens, 1, cost, model)
        return result


def unpatch_openai() -> None:
    """Restore original OpenAI client, undoing patch_openai().

    Safe to call even if patch_openai() was never called.
    """
    if "openai_init" in _originals:
        cls = _originals.pop("openai_cls")
        cls.__init__ = _originals.pop("openai_init")
    if "openai_legacy_create" in _originals:
        chat = _originals.pop("openai_legacy_chat")
        chat.create = _originals.pop("openai_legacy_create")


def patch_anthropic(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch Anthropic client to auto-trace messages.create.

    Works with the anthropic SDK where messages is an instance attribute.
    Safe to call even if anthropic is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard. Each call's cost/tokens are
            fed into ``guard.consume()`` automatically.
    """
    try:
        import anthropic  # noqa: F811
    except ImportError:
        return

    client_cls = getattr(anthropic, "Anthropic", None)
    if client_cls is None:
        return

    if "anthropic_init" in _originals:
        return  # already patched

    original_init = client_cls.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_anthropic_instance(self, tracer, budget_guard)

    _originals["anthropic_init"] = original_init
    _originals["anthropic_cls"] = client_cls
    client_cls.__init__ = patched_init  # type: ignore[attr-defined]


def _patch_anthropic_instance(client: Any, tracer: Any, budget_guard: Any = None) -> None:
    """Patch a single Anthropic client instance's messages.create."""
    messages = getattr(client, "messages", None)
    if messages is None:
        return
    original_create = messages.create

    @functools.wraps(original_create)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        with tracer.trace(f"llm.anthropic.{model}") as ctx:
            result = original_create(*args, **kwargs)
            usage = getattr(result, "usage", None)
            if usage is not None:
                input_tokens = getattr(usage, "input_tokens", 0)
                output_tokens = getattr(usage, "output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                from agentguard.cost import estimate_cost

                cost = estimate_cost(model, input_tokens, output_tokens, provider="anthropic")
                event_data: dict = {
                    "model": model,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                }
                ctx.event("llm.result", data=event_data, cost_usd=cost if cost > 0 else None)
                if budget_guard is not None:
                    _consume_budget(budget_guard, ctx, total_tokens, 1, cost, model)
            return result

    messages.create = traced_create  # type: ignore[attr-defined]


def unpatch_anthropic() -> None:
    """Restore original Anthropic client, undoing patch_anthropic().

    Safe to call even if patch_anthropic() was never called.
    """
    if "anthropic_init" in _originals:
        cls = _originals.pop("anthropic_cls")
        cls.__init__ = _originals.pop("anthropic_init")


# --- Async decorators ---


def async_trace_agent(tracer: Any, name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator that wraps an async function in a top-level trace span.

    Usage::

        @async_trace_agent(tracer)
        async def my_agent(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"agent.{fn.__name__}"

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with tracer.trace(span_name) as ctx:
                kwargs["_trace_ctx"] = ctx
                try:
                    return await fn(*args, **kwargs)
                except Exception:
                    raise
                finally:
                    kwargs.pop("_trace_ctx", None)

        @functools.wraps(fn)
        async def simple_wrapper(*args: Any, **kwargs: Any) -> Any:
            async with tracer.trace(span_name):
                return await fn(*args, **kwargs)

        import inspect

        sig = inspect.signature(fn)
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        has_trace_ctx = "_trace_ctx" in sig.parameters

        if has_var_keyword or has_trace_ctx:
            return wrapper  # type: ignore[return-value]
        return simple_wrapper  # type: ignore[return-value]

    return decorator


def async_trace_tool(tracer: Any, name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator that wraps an async function in a tool span.

    Usage::

        @async_trace_tool(tracer)
        async def search(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"tool.{fn.__name__}"

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with tracer.trace(span_name) as ctx:
                result = await fn(*args, **kwargs)
                ctx.event("tool.result", data={"result": str(result)[:500]})
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


# --- Async patches ---


def patch_openai_async(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch OpenAI AsyncOpenAI client to auto-trace async completions.

    Safe to call even if openai is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard. Each call's cost/tokens are
            fed into ``guard.consume()`` automatically.
    """
    try:
        import openai  # noqa: F811
    except ImportError:
        return

    client_cls = getattr(openai, "AsyncOpenAI", None)
    if client_cls is None:
        return

    if "openai_async_init" in _originals:
        return  # already patched

    original_init = client_cls.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_openai_async_instance(self, tracer, budget_guard)

    _originals["openai_async_init"] = original_init
    _originals["openai_async_cls"] = client_cls
    client_cls.__init__ = patched_init  # type: ignore[attr-defined]


def _patch_openai_async_instance(client: Any, tracer: Any, budget_guard: Any = None) -> None:
    """Patch a single AsyncOpenAI client instance."""
    chat = getattr(client, "chat", None)
    if chat is None:
        return
    completions = getattr(chat, "completions", None)
    if completions is None:
        return
    original_create = completions.create

    @functools.wraps(original_create)
    async def traced_create(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        async with tracer.trace(f"llm.openai.{model}") as ctx:
            result = await original_create(*args, **kwargs)
            usage = getattr(result, "usage", None)
            if usage is not None:
                input_tokens = getattr(usage, "prompt_tokens", 0)
                output_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)
                from agentguard.cost import estimate_cost

                cost = estimate_cost(model, input_tokens, output_tokens, provider="openai")
                event_data: dict = {
                    "model": model,
                    "usage": {
                        "prompt_tokens": input_tokens,
                        "completion_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    },
                }
                ctx.event("llm.result", data=event_data, cost_usd=cost if cost > 0 else None)
                if budget_guard is not None:
                    _consume_budget(budget_guard, ctx, total_tokens, 1, cost, model)
            return result

    completions.create = traced_create  # type: ignore[attr-defined]


def unpatch_openai_async() -> None:
    """Restore original AsyncOpenAI client."""
    if "openai_async_init" in _originals:
        cls = _originals.pop("openai_async_cls")
        cls.__init__ = _originals.pop("openai_async_init")


def patch_anthropic_async(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch Anthropic AsyncAnthropic client to auto-trace async calls.

    Safe to call even if anthropic is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard. Each call's cost/tokens are
            fed into ``guard.consume()`` automatically.
    """
    try:
        import anthropic  # noqa: F811
    except ImportError:
        return

    client_cls = getattr(anthropic, "AsyncAnthropic", None)
    if client_cls is None:
        return

    if "anthropic_async_init" in _originals:
        return

    original_init = client_cls.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_anthropic_async_instance(self, tracer, budget_guard)

    _originals["anthropic_async_init"] = original_init
    _originals["anthropic_async_cls"] = client_cls
    client_cls.__init__ = patched_init  # type: ignore[attr-defined]


def _patch_anthropic_async_instance(client: Any, tracer: Any, budget_guard: Any = None) -> None:
    """Patch a single AsyncAnthropic client instance."""
    messages = getattr(client, "messages", None)
    if messages is None:
        return
    original_create = messages.create

    @functools.wraps(original_create)
    async def traced_create(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        async with tracer.trace(f"llm.anthropic.{model}") as ctx:
            result = await original_create(*args, **kwargs)
            usage = getattr(result, "usage", None)
            if usage is not None:
                input_tokens = getattr(usage, "input_tokens", 0)
                output_tokens = getattr(usage, "output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                from agentguard.cost import estimate_cost

                cost = estimate_cost(model, input_tokens, output_tokens, provider="anthropic")
                event_data: dict = {
                    "model": model,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                }
                ctx.event("llm.result", data=event_data, cost_usd=cost if cost > 0 else None)
                if budget_guard is not None:
                    _consume_budget(budget_guard, ctx, total_tokens, 1, cost, model)
            return result

    messages.create = traced_create  # type: ignore[attr-defined]


def unpatch_anthropic_async() -> None:
    """Restore original AsyncAnthropic client."""
    if "anthropic_async_init" in _originals:
        cls = _originals.pop("anthropic_async_cls")
        cls.__init__ = _originals.pop("anthropic_async_init")
