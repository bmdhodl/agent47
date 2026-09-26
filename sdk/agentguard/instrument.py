"""Auto-instrumentation decorators and monkey-patches."""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, TypeVar

from agentguard._billing import (
    _check_budget_before_request,
    _consume_budget,
    _emit_llm_result,
    _emit_stream_final,
)
from agentguard.instrument_stream import (
    ensure_openai_stream_usage,
    is_raw_response_call,
    run_traced_create,
    run_traced_create_async,
)

F = TypeVar("F", bound=Callable[..., Any])

# Store originals for unpatch support
_originals: Dict[str, Any] = {}


def _traced_provider_create(
    original: Any,
    tracer: Any,
    budget_guard: Any,
    provider: str,
    args: tuple,
    kwargs: Dict[str, Any],
    *,
    wrap_stream: bool,
) -> Any:
    return run_traced_create(
        original,
        tracer,
        budget_guard,
        provider,
        args,
        kwargs,
        wrap_stream=wrap_stream,
        check_budget=_check_budget_before_request,
        emit_result=_emit_llm_result,
        consume_budget=_consume_budget,
    )


async def _traced_provider_create_async(
    original: Any,
    tracer: Any,
    budget_guard: Any,
    provider: str,
    args: tuple,
    kwargs: Dict[str, Any],
    *,
    wrap_stream: bool,
) -> Any:
    return await run_traced_create_async(
        original,
        tracer,
        budget_guard,
        provider,
        args,
        kwargs,
        wrap_stream=wrap_stream,
        check_budget=_check_budget_before_request,
        emit_result=_emit_llm_result,
        consume_budget=_consume_budget,
    )


# ---------------------------------------------------------------------------
# Sync decorators
# ---------------------------------------------------------------------------


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

        @functools.wraps(fn)
        def simple_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.trace(span_name):
                return fn(*args, **kwargs)

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
        tool_name = span_name[len("tool."):] if span_name.startswith("tool.") else span_name

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.trace(span_name) as ctx:
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:
                    ctx.event(
                        "tool.error",
                        data={
                            "tool_name": tool_name,
                            "error_type": type(exc).__name__,
                            "message": str(exc)[:500],
                        },
                    )
                    raise
                ctx.event(
                    "tool.result",
                    data={"tool_name": tool_name, "result": str(result)[:500]},
                )
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Sync patches
# ---------------------------------------------------------------------------


def patch_openai(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch OpenAI client to auto-trace chat completions.

    Works with openai >= 1.0 (instance-based client) and < 1.0 (module-based).
    Safe to call even if openai is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard for automatic budget tracking.
    """
    try:
        import openai
    except ImportError:
        return

    client_cls = getattr(openai, "OpenAI", None)
    if client_cls is not None:
        if "openai_init" in _originals:
            return
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
    """Patch a single OpenAI client's chat.completions.create and Responses API."""
    _patch_openai_responses(client, _traced_responses_method, tracer, budget_guard)
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


def _patch_openai_responses(client: Any, wrap: Any, tracer: Any, budget_guard: Any) -> None:
    """Patch responses.create and responses.parse (openai>=1.66).

    responses.stream() and with_streaming_response / with_raw_response call
    the patched create, so they are counted too.
    """
    responses = getattr(client, "responses", None)
    if responses is None:
        return
    for name in ("create", "parse"):
        original = getattr(responses, name, None)
        if original is not None:
            setattr(responses, name, wrap(original, tracer, budget_guard))


def _traced_responses_method(original: Any, tracer: Any, budget_guard: Any) -> Any:
    @functools.wraps(original)
    def traced(*args: Any, **kwargs: Any) -> Any:
        return _traced_openai_call(original, tracer, budget_guard, args, kwargs)

    return traced


def _traced_openai_create(
    original: Any, tracer: Any, budget_guard: Any, *args: Any, **kwargs: Any
) -> Any:
    """Sync Chat Completions create. Streams ask for a final usage chunk."""
    return _traced_openai_call(
        original, tracer, budget_guard, args, ensure_openai_stream_usage(kwargs)
    )


def _traced_openai_call(
    original: Any, tracer: Any, budget_guard: Any, args: tuple, kwargs: Dict[str, Any]
) -> Any:
    """Sync OpenAI call. A stored budget reserves before a non-stream send."""
    if (
        getattr(budget_guard, "_store", None) is not None
        and not kwargs.get("stream")
        and not is_raw_response_call(kwargs)
    ):
        from ._reservation_path import traced_openai_reserved

        return traced_openai_reserved(original, tracer, budget_guard, args, kwargs)
    return _traced_provider_create(
        original,
        tracer,
        budget_guard,
        "openai",
        args,
        kwargs,
        wrap_stream=bool(kwargs.get("stream")),
    )


def unpatch_openai() -> None:
    """Restore original OpenAI client, undoing patch_openai()."""
    if "openai_init" in _originals:
        cls = _originals.pop("openai_cls")
        cls.__init__ = _originals.pop("openai_init")
    if "openai_legacy_create" in _originals:
        chat = _originals.pop("openai_legacy_chat")
        chat.create = _originals.pop("openai_legacy_create")


def patch_anthropic(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch Anthropic client to auto-trace messages.create.

    Safe to call even if anthropic is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard for automatic budget tracking.
    """
    try:
        import anthropic
    except ImportError:
        return

    client_cls = getattr(anthropic, "Anthropic", None)
    if client_cls is None:
        return

    if "anthropic_init" in _originals:
        return

    original_init = client_cls.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_anthropic_instance(self, tracer, budget_guard)

    _originals["anthropic_init"] = original_init
    _originals["anthropic_cls"] = client_cls
    client_cls.__init__ = patched_init  # type: ignore[attr-defined]


def _patch_anthropic_instance(client: Any, tracer: Any, budget_guard: Any = None) -> None:
    """Patch a single Anthropic client instance's messages.create and stream."""
    messages = getattr(client, "messages", None)
    if messages is None:
        return
    original_create = messages.create

    @functools.wraps(original_create)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        return _traced_provider_create(
            original_create,
            tracer,
            budget_guard,
            "anthropic",
            args,
            kwargs,
            wrap_stream=bool(kwargs.get("stream")),
        )

    messages.create = traced_create  # type: ignore[attr-defined]
    original_stream = getattr(messages, "stream", None)
    if original_stream is None:
        return

    @functools.wraps(original_stream)
    def traced_stream(*args: Any, **kwargs: Any) -> Any:
        return _traced_provider_create(
            original_stream,
            tracer,
            budget_guard,
            "anthropic",
            args,
            kwargs,
            wrap_stream=True,
        )

    messages.stream = traced_stream  # type: ignore[attr-defined]


def unpatch_anthropic() -> None:
    """Restore original Anthropic client, undoing patch_anthropic()."""
    if "anthropic_init" in _originals:
        cls = _originals.pop("anthropic_cls")
        cls.__init__ = _originals.pop("anthropic_init")


# ---------------------------------------------------------------------------
# Async decorators
# ---------------------------------------------------------------------------


def async_trace_agent(tracer: Any, name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator that wraps an async function in a top-level trace span.

    Requires an ``AsyncTracer`` or tracer-compatible object whose ``trace()``
    method returns an async context manager. Use ``trace_agent`` with the sync
    ``Tracer``.

    Usage::

        @async_trace_agent(tracer)
        async def my_agent(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"agent.{fn.__name__}"

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with _async_trace_context(tracer, span_name, "async_trace_agent") as ctx:
                kwargs["_trace_ctx"] = ctx
                try:
                    return await fn(*args, **kwargs)
                except Exception:
                    raise
                finally:
                    kwargs.pop("_trace_ctx", None)

        @functools.wraps(fn)
        async def simple_wrapper(*args: Any, **kwargs: Any) -> Any:
            async with _async_trace_context(tracer, span_name, "async_trace_agent"):
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

    Requires an ``AsyncTracer`` or tracer-compatible object whose ``trace()``
    method returns an async context manager. Use ``trace_tool`` with the sync
    ``Tracer``.

    Usage::

        @async_trace_tool(tracer)
        async def search(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        span_name = name or f"tool.{fn.__name__}"
        tool_name = span_name[len("tool."):] if span_name.startswith("tool.") else span_name

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with _async_trace_context(tracer, span_name, "async_trace_tool") as ctx:
                try:
                    result = await fn(*args, **kwargs)
                except Exception as exc:
                    ctx.event(
                        "tool.error",
                        data={
                            "tool_name": tool_name,
                            "error_type": type(exc).__name__,
                            "message": str(exc)[:500],
                        },
                    )
                    raise
                ctx.event(
                    "tool.result",
                    data={"tool_name": tool_name, "result": str(result)[:500]},
                )
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


def _async_trace_context(tracer: Any, span_name: str, decorator_name: str) -> Any:
    """Return an async trace context or raise a clear tracer-mismatch error."""
    trace = getattr(tracer, "trace", None)
    if not callable(trace):
        raise TypeError(
            f"{decorator_name} requires an AsyncTracer-compatible tracer with trace(). "
            "Use AsyncTracer with async decorators, or use the sync decorator with Tracer."
        )
    context_manager = trace(span_name)
    if not (
        hasattr(context_manager, "__aenter__")
        and hasattr(context_manager, "__aexit__")
    ):
        raise TypeError(
            f"{decorator_name} requires AsyncTracer; got "
            f"{type(tracer).__name__}. Use AsyncTracer with async decorators, "
            "or use the sync decorator with Tracer."
        )
    return context_manager


# ---------------------------------------------------------------------------
# Async patches
# ---------------------------------------------------------------------------


def patch_openai_async(tracer: Any, budget_guard: Any = None) -> None:
    """Monkey-patch OpenAI AsyncOpenAI client to auto-trace async completions.

    Safe to call even if openai is not installed — silently returns.

    Args:
        tracer: Tracer instance for emitting events.
        budget_guard: Optional BudgetGuard for automatic budget tracking.
    """
    try:
        import openai
    except ImportError:
        return

    client_cls = getattr(openai, "AsyncOpenAI", None)
    if client_cls is None:
        return

    if "openai_async_init" in _originals:
        return

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
    _patch_openai_responses(client, _traced_async_openai_method, tracer, budget_guard)
    chat = getattr(client, "chat", None)
    if chat is None:
        return
    completions = getattr(chat, "completions", None)
    if completions is None:
        return
    original_create = completions.create
    traced = _traced_async_openai_method(original_create, tracer, budget_guard)

    @functools.wraps(original_create)
    async def traced_create(*args: Any, **kwargs: Any) -> Any:
        return await traced(*args, **ensure_openai_stream_usage(kwargs))

    completions.create = traced_create  # type: ignore[attr-defined]


def _traced_async_openai_method(original: Any, tracer: Any, budget_guard: Any) -> Any:
    @functools.wraps(original)
    async def traced(*args: Any, **kwargs: Any) -> Any:
        return await _traced_provider_create_async(
            original,
            tracer,
            budget_guard,
            "openai",
            args,
            kwargs,
            wrap_stream=bool(kwargs.get("stream")),
        )

    return traced


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
        budget_guard: Optional BudgetGuard for automatic budget tracking.
    """
    try:
        import anthropic
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
    """Patch a single AsyncAnthropic client instance's messages.create and stream."""
    messages = getattr(client, "messages", None)
    if messages is None:
        return
    original_create = messages.create

    @functools.wraps(original_create)
    async def traced_create(*args: Any, **kwargs: Any) -> Any:
        return await _traced_provider_create_async(
            original_create,
            tracer,
            budget_guard,
            "anthropic",
            args,
            kwargs,
            wrap_stream=bool(kwargs.get("stream")),
        )

    messages.create = traced_create  # type: ignore[attr-defined]
    original_stream = getattr(messages, "stream", None)
    if original_stream is None:
        return

    @functools.wraps(original_stream)
    def traced_stream(*args: Any, **kwargs: Any) -> Any:
        from agentguard.instrument_stream import open_provider_async_stream

        return open_provider_async_stream(
            original_stream,
            tracer,
            budget_guard,
            args,
            kwargs,
            check_budget=_check_budget_before_request,
            emit_final=_emit_stream_final,
        )

    messages.stream = traced_stream  # type: ignore[attr-defined]


def unpatch_anthropic_async() -> None:
    """Restore original AsyncAnthropic client."""
    if "anthropic_async_init" in _originals:
        cls = _originals.pop("anthropic_async_cls")
        cls.__init__ = _originals.pop("anthropic_async_init")
