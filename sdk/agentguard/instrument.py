"""Auto-instrumentation decorators and monkey-patches."""
from __future__ import annotations

import functools
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


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


def patch_openai(tracer: Any) -> None:
    """Monkey-patch OpenAI's ChatCompletion.create to auto-trace calls.

    Safe to call even if openai is not installed — silently returns.
    """
    try:
        import openai  # noqa: F811
    except ImportError:
        return

    _original = None

    # Support openai >= 1.0 (client-based) and < 1.0 (module-based)
    client_cls = getattr(openai, "OpenAI", None)
    if client_cls is not None:
        # openai >= 1.0: patch the completions create method on the class
        chat_completions = getattr(
            getattr(client_cls, "chat", None), "completions", None
        )
        if chat_completions is not None:
            _original = getattr(chat_completions, "create", None)
    else:
        # openai < 1.0
        chat = getattr(openai, "ChatCompletion", None)
        if chat is not None:
            _original = getattr(chat, "create", None)

    if _original is None:
        return

    @functools.wraps(_original)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        with tracer.trace(f"llm.openai.{model}") as ctx:
            result = _original(*args, **kwargs)
            # Try to extract usage
            usage = getattr(result, "usage", None)
            if usage is not None:
                ctx.event(
                    "llm.result",
                    data={
                        "model": model,
                        "usage": {
                            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                            "completion_tokens": getattr(usage, "completion_tokens", 0),
                            "total_tokens": getattr(usage, "total_tokens", 0),
                        },
                    },
                )
            return result

    # Patch it back
    if client_cls is not None and chat_completions is not None:
        chat_completions.create = traced_create  # type: ignore[attr-defined]
    else:
        chat = getattr(openai, "ChatCompletion", None)
        if chat is not None:
            chat.create = traced_create  # type: ignore[attr-defined]


def patch_anthropic(tracer: Any) -> None:
    """Monkey-patch Anthropic's messages.create to auto-trace calls.

    Safe to call even if anthropic is not installed — silently returns.
    """
    try:
        import anthropic  # noqa: F811
    except ImportError:
        return

    client_cls = getattr(anthropic, "Anthropic", None)
    if client_cls is None:
        return

    messages = getattr(client_cls, "messages", None)
    if messages is None:
        return

    _original = getattr(messages, "create", None)
    if _original is None:
        return

    @functools.wraps(_original)
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        model = kwargs.get("model", "unknown")
        with tracer.trace(f"llm.anthropic.{model}") as ctx:
            result = _original(*args, **kwargs)
            usage = getattr(result, "usage", None)
            if usage is not None:
                ctx.event(
                    "llm.result",
                    data={
                        "model": model,
                        "usage": {
                            "input_tokens": getattr(usage, "input_tokens", 0),
                            "output_tokens": getattr(usage, "output_tokens", 0),
                        },
                    },
                )
            return result

    messages.create = traced_create  # type: ignore[attr-defined]
