"""Private stream wrappers for provider patches. Not part of the public API."""
from __future__ import annotations

import inspect
import sys
import threading
from typing import Any, Callable, Dict

OnFinal = Callable[[Any, Any], None]


def ensure_openai_stream_usage(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Request final usage on OpenAI streams unless the caller set include_usage."""
    if not kwargs.get("stream"):
        return kwargs
    options = kwargs.get("stream_options")
    if options is None:
        updated = dict(kwargs)
        updated["stream_options"] = {"include_usage": True}
        return updated
    if isinstance(options, dict) and "include_usage" not in options:
        updated = dict(kwargs)
        merged = dict(options)
        merged["include_usage"] = True
        updated["stream_options"] = merged
        return updated
    return kwargs


def chunk_usage(chunk: Any) -> Any:
    """Return a usage payload from a stream chunk or final message, if present."""
    if chunk is None:
        return None
    usage = getattr(chunk, "usage", None)
    if usage is None and isinstance(chunk, dict):
        usage = chunk.get("usage")
    if usage is None:
        message = getattr(chunk, "message", None)
        if message is not None:
            usage = getattr(message, "usage", None)
    return usage


class CountedStream:
    """Proxy that records final usage once, then closes the held trace span."""

    def __init__(
        self,
        inner: Any,
        on_final: OnFinal,
        span_cm: Any,
        *,
        async_span: bool = False,
        factory: Any = None,
        on_open: Any = None,
    ) -> None:
        self._inner = inner
        self._factory = factory
        self._on_open = on_open
        self._entered: Any = None
        self._on_final = on_final
        self._span_cm = span_cm
        self._async_span = async_span
        self._usage: Any = None
        self._response: Any = None
        self._done = False
        self._opened = factory is None
        self._lock = threading.Lock()

    def _source(self) -> Any:
        if self._entered is not None:
            return self._entered
        return self._inner

    def _open_sync(self) -> None:
        if self._opened:
            return
        self._opened = True
        ctx = self._span_cm.__enter__()
        try:
            if self._on_open is not None:
                self._on_open(ctx)
            inner = self._factory() if self._factory is not None else self._inner
            self._inner = inner
        except BaseException:
            self._span_cm.__exit__(*sys.exc_info())
            self._span_cm = None
            self._done = True
            raise

    async def _open_async(self) -> None:
        if self._opened:
            return
        self._opened = True
        ctx = await self._span_cm.__aenter__()
        try:
            if self._on_open is not None:
                self._on_open(ctx)
            inner = self._factory() if self._factory is not None else self._inner
            if inspect.isawaitable(inner):
                inner = await inner
            self._inner = inner
        except BaseException:
            await self._span_cm.__aexit__(*sys.exc_info())
            self._span_cm = None
            self._done = True
            raise

    def _capture(self, chunk: Any) -> None:
        usage = chunk_usage(chunk)
        if usage is not None:
            self._usage = usage
            self._response = chunk

    def _harvest(self) -> None:
        if self._usage is not None:
            return
        getter = getattr(self._source(), "get_final_message", None)
        if not callable(getter):
            return
        try:
            result = getter()
        except Exception:
            return
        if inspect.isawaitable(result):
            return
        self._capture(result)

    async def _aharvest(self) -> None:
        if self._usage is not None:
            return
        getter = getattr(self._source(), "get_final_message", None)
        if not callable(getter):
            return
        try:
            result = getter()
            if inspect.isawaitable(result):
                result = await result
        except Exception:
            return
        self._capture(result)

    def _finish(self) -> None:
        if not self._opened:
            return
        with self._lock:
            if self._done:
                return
            self._done = True
        self._harvest()
        try:
            self._on_final(self._usage, self._response)
        finally:
            if not self._async_span and self._span_cm is not None:
                cm, self._span_cm = self._span_cm, None
                cm.__exit__(None, None, None)

    async def _afinish(self) -> None:
        if not self._opened:
            return
        first = False
        with self._lock:
            if not self._done:
                self._done = True
                first = True
        try:
            if first:
                await self._aharvest()
                self._on_final(self._usage, self._response)
        finally:
            if self._span_cm is not None:
                cm, self._span_cm = self._span_cm, None
                if self._async_span:
                    await cm.__aexit__(None, None, None)
                else:
                    cm.__exit__(None, None, None)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._source(), name)

    def __iter__(self) -> Any:
        self._open_sync()
        try:
            for chunk in self._source():
                self._capture(chunk)
                yield chunk
        except BaseException:
            self._finish()
            raise
        self._finish()

    def __aiter__(self) -> Any:
        return self._async_chunks()

    async def _async_chunks(self) -> Any:
        await self._open_async()
        try:
            async for chunk in self._source():
                self._capture(chunk)
                yield chunk
        except BaseException:
            await self._afinish()
            raise
        await self._afinish()

    def __enter__(self) -> "CountedStream":
        self._open_sync()
        enter = getattr(self._inner, "__enter__", None)
        if callable(enter):
            entered = enter()
            if entered is not self._inner and entered is not self:
                self._entered = entered
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        exit_fn = getattr(self._inner, "__exit__", None)
        try:
            if callable(exit_fn):
                return exit_fn(exc_type, exc, tb)
            return None
        finally:
            self._finish()

    async def __aenter__(self) -> "CountedStream":
        await self._open_async()
        enter = getattr(self._inner, "__aenter__", None)
        if callable(enter):
            entered = enter()
            if inspect.isawaitable(entered):
                entered = await entered
            if entered is not self._inner and entered is not self:
                self._entered = entered
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        exit_fn = getattr(self._inner, "__aexit__", None)
        try:
            if callable(exit_fn):
                result = exit_fn(exc_type, exc, tb)
                if inspect.isawaitable(result):
                    return await result
                return result
            return None
        finally:
            await self._afinish()

    def get_final_message(self, *args: Any, **kwargs: Any) -> Any:
        self._open_sync()
        getter = self._source().get_final_message
        result = getter(*args, **kwargs)
        if inspect.isawaitable(result):
            return self._await_final_message(result)
        self._capture(result)
        self._finish()
        return result

    async def _await_final_message(self, result: Any) -> Any:
        message = await result
        self._capture(message)
        await self._afinish()
        return message

    def close(self) -> Any:
        closer = getattr(self._source(), "close", None)
        try:
            result = closer() if callable(closer) else None
        except BaseException:
            self._finish()
            raise
        if inspect.isawaitable(result):
            return self._await_close(result)
        self._finish()
        return result

    async def aclose(self) -> None:
        closer = getattr(self._source(), "aclose", None)
        try:
            if callable(closer):
                result = closer()
                if inspect.isawaitable(result):
                    await result
        finally:
            await self._afinish()

    async def _await_close(self, result: Any) -> Any:
        try:
            return await result
        finally:
            await self._afinish()


def emit_stream_final(
    ctx: Any,
    budget_guard: Any,
    model: str,
    provider: str,
    usage: Any,
    response: Any,
    emit_result: Callable[..., None],
    consume_budget: Callable[..., None],
) -> None:
    """Bill a completed stream once. Count the dispatched call if usage is missing."""
    resolved_usage = usage
    if resolved_usage is None and response is not None:
        resolved_usage = getattr(response, "usage", None)
    if resolved_usage is not None:
        emit_result(
            ctx, budget_guard, model, provider, resolved_usage, response=response
        )
        return
    ctx.event(
        "llm.result",
        data={"model": model, "provider": provider, "usage": None, "stream": True},
    )
    if budget_guard is not None:
        consume_budget(budget_guard, ctx, 0, 1, 0.0, model)


def run_traced_create(
    original: Any,
    tracer: Any,
    budget_guard: Any,
    provider: str,
    args: tuple,
    kwargs: Dict[str, Any],
    *,
    wrap_stream: bool,
    check_budget: Callable[..., None],
    emit_result: Callable[..., None],
    consume_budget: Callable[..., None],
) -> Any:
    """Sync provider call: preflight, then bill a response or wrap a stream."""
    model = str(kwargs.get("model", "unknown"))
    if wrap_stream and provider == "openai":
        kwargs = ensure_openai_stream_usage(kwargs)
    span_cm = tracer.trace(
        f"llm.{provider}.{model}",
        data={"model": model, "provider": provider},
    )
    ctx = span_cm.__enter__()
    try:
        check_budget(budget_guard, ctx, model)
        result = original(*args, **kwargs)
    except BaseException:
        span_cm.__exit__(*sys.exc_info())
        raise
    if wrap_stream:
        def on_final(usage: Any, response: Any) -> None:
            emit_stream_final(
                ctx, budget_guard, model, provider, usage, response,
                emit_result, consume_budget,
            )

        return CountedStream(result, on_final, span_cm, async_span=False)
    try:
        emit_result(
            ctx, budget_guard, model, provider, getattr(result, "usage", None), response=result
        )
    except BaseException:
        span_cm.__exit__(*sys.exc_info())
        raise
    span_cm.__exit__(None, None, None)
    return result


async def run_traced_create_async(
    original: Any,
    tracer: Any,
    budget_guard: Any,
    provider: str,
    args: tuple,
    kwargs: Dict[str, Any],
    *,
    wrap_stream: bool,
    check_budget: Callable[..., None],
    emit_result: Callable[..., None],
    consume_budget: Callable[..., None],
) -> Any:
    """Async provider call: preflight, then bill a response or wrap a stream."""
    model = str(kwargs.get("model", "unknown"))
    if wrap_stream and provider == "openai":
        kwargs = ensure_openai_stream_usage(kwargs)
    span_cm = tracer.trace(
        f"llm.{provider}.{model}",
        data={"model": model, "provider": provider},
    )
    ctx = await span_cm.__aenter__()
    try:
        check_budget(budget_guard, ctx, model)
        result = original(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
    except BaseException:
        await span_cm.__aexit__(*sys.exc_info())
        raise
    if wrap_stream:
        def on_final(usage: Any, response: Any) -> None:
            emit_stream_final(
                ctx, budget_guard, model, provider, usage, response,
                emit_result, consume_budget,
            )

        return CountedStream(result, on_final, span_cm, async_span=True)
    try:
        emit_result(
            ctx, budget_guard, model, provider, getattr(result, "usage", None), response=result
        )
    except BaseException:
        await span_cm.__aexit__(*sys.exc_info())
        raise
    await span_cm.__aexit__(None, None, None)
    return result
