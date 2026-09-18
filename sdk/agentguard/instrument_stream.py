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


def _usage_mapping(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return {key: value for key, value in usage.items() if not str(key).startswith("_")}
    mapping: Dict[str, Any] = {}
    source = getattr(usage, "__dict__", None)
    if isinstance(source, dict):
        mapping.update(
            {key: value for key, value in source.items() if not str(key).startswith("_")}
        )
    for name in (
        "input_tokens",
        "output_tokens",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
    ):
        if name not in mapping and hasattr(usage, name):
            mapping[name] = getattr(usage, name)
    return mapping


def merge_usage(current: Any, incoming: Any) -> Any:
    """Keep complementary stream usage fields instead of replacing the payload."""
    if incoming is None:
        return current
    if current is None:
        return incoming
    merged = _usage_mapping(current)
    extra = _usage_mapping(incoming)
    if not extra:
        return current
    for key, value in extra.items():
        if value is None:
            continue
        previous = merged.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(previous, (int, float)) and not isinstance(previous, bool):
                merged[key] = max(int(previous), int(value))
            else:
                merged[key] = int(value)
            continue
        if previous in (None, 0, ""):
            merged[key] = value
    input_tokens = int(merged.get("input_tokens") or merged.get("prompt_tokens") or 0)
    output_tokens = int(merged.get("output_tokens") or merged.get("completion_tokens") or 0)
    cache_tokens = int(merged.get("cache_read_input_tokens") or 0) + int(
        merged.get("cache_creation_input_tokens") or 0
    )
    parts = input_tokens + output_tokens + cache_tokens
    if parts > int(merged.get("total_tokens") or 0):
        merged["total_tokens"] = parts
    return merged


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
        self._sync_iter: Any = None
        self._async_iter: Any = None
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
        if usage is None:
            return
        self._usage = merge_usage(self._usage, usage)
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

    def _close_span(self, exc_info: Any = None) -> None:
        if self._async_span or self._span_cm is None:
            return
        cm, self._span_cm = self._span_cm, None
        if exc_info is None:
            cm.__exit__(None, None, None)
        else:
            cm.__exit__(*exc_info)

    async def _aclose_span(self, exc_info: Any = None) -> None:
        if self._span_cm is None:
            return
        cm, self._span_cm = self._span_cm, None
        info = (None, None, None) if exc_info is None else exc_info
        if self._async_span:
            await cm.__aexit__(*info)
        else:
            cm.__exit__(*info)

    def _finish(self, exc_info: Any = None) -> None:
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
            self._close_span(exc_info)

    async def _afinish(self, exc_info: Any = None) -> None:
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
            await self._aclose_span(exc_info)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._source(), name)

    def __iter__(self) -> "CountedStream":
        self._open_sync()
        if self._sync_iter is None:
            self._sync_iter = iter(self._source())
        return self

    def __next__(self) -> Any:
        iterator = self.__iter__()
        try:
            chunk = next(iterator._sync_iter)
        except StopIteration:
            self._finish()
            raise
        except BaseException:
            self._finish(sys.exc_info())
            raise
        self._capture(chunk)
        return chunk

    def __aiter__(self) -> "CountedStream":
        return self

    async def __anext__(self) -> Any:
        await self._open_async()
        if self._async_iter is None:
            source = self._source()
            iterator = source.__aiter__()
            if inspect.isawaitable(iterator):
                iterator = await iterator
            self._async_iter = iterator
        try:
            chunk = await self._async_iter.__anext__()
        except StopAsyncIteration:
            await self._afinish()
            raise
        except BaseException:
            await self._afinish(sys.exc_info())
            raise
        self._capture(chunk)
        return chunk

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
            self._finish(None if exc_type is None else (exc_type, exc, tb))

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
            await self._afinish(None if exc_type is None else (exc_type, exc, tb))

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
            self._finish(sys.exc_info())
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
        except BaseException:
            await self._afinish(sys.exc_info())
            raise
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
