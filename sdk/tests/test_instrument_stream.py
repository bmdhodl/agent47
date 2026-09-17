"""Streamed provider patches bill final usage once."""
import asyncio
from types import SimpleNamespace

import pytest

from agentguard import AsyncTracer, BudgetExceeded, BudgetGuard, Tracer, instrument
from agentguard.instrument_stream import ensure_openai_stream_usage


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


def _openai_chunks(total_tokens=200):
    usage = SimpleNamespace(
        prompt_tokens=120,
        completion_tokens=80,
        total_tokens=total_tokens,
    )
    return [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="a"))], usage=None),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="b"))], usage=None),
        SimpleNamespace(choices=[], usage=usage),
    ]


class SyncStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.usage = None

    def __iter__(self):
        return iter(self._chunks)


class AsyncStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.usage = None

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for chunk in self._chunks:
            yield chunk


class MessageStream:
    def __init__(self, message, events=None):
        self._message = message
        self._events = events or [SimpleNamespace(type="delta", usage=None)]
        self.text_stream = iter(["ok"])

    def __iter__(self):
        return iter(self._events)

    def get_final_message(self):
        return self._message


class StreamManager:
    def __init__(self, stream):
        self._stream = stream

    def __enter__(self):
        return self._stream

    def __exit__(self, exc_type, exc, tb):
        return False


class AsyncMessageStream:
    def __init__(self, message):
        self._message = message
        self.text_stream = _aiter_text("ok")

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        yield SimpleNamespace(type="delta", usage=None)

    async def get_final_message(self):
        return self._message


class AsyncStreamManager:
    def __init__(self, stream):
        self._stream = stream

    async def __aenter__(self):
        return self._stream

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _aiter_text(text):
    async def gen():
        yield text

    return gen()


def _anthropic_message(input_tokens=80, output_tokens=40):
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
    )


def test_ensure_openai_stream_usage_injects_and_respects_false():
    injected = ensure_openai_stream_usage({"stream": True, "model": "gpt-4o"})
    assert injected["stream_options"]["include_usage"] is True
    merged = ensure_openai_stream_usage(
        {"stream": True, "stream_options": {"include_obfuscation": True}}
    )
    assert merged["stream_options"]["include_usage"] is True
    assert merged["stream_options"]["include_obfuscation"] is True
    kept = ensure_openai_stream_usage(
        {"stream": True, "stream_options": {"include_usage": False}}
    )
    assert kept["stream_options"]["include_usage"] is False
    unchanged = ensure_openai_stream_usage({"model": "gpt-4o"})
    assert "stream_options" not in unchanged


def test_openai_stream_bills_final_usage_once():
    sent = []
    chunks = _openai_chunks()

    def create(**kwargs):
        sent.append(kwargs)
        return SyncStream(chunks)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    sink = Sink()
    instrument._patch_openai_instance(client, Tracer(sink=sink), guard)
    stream = client.chat.completions.create(model="gpt-4o-mini", stream=True)
    received = list(stream)
    assert len(received) == 3
    assert sent[0]["stream_options"]["include_usage"] is True
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 200
    results = [e for e in sink.events if e.get("name") == "llm.result"]
    assert len(results) == 1


def test_openai_stream_respects_explicit_include_usage_false():
    sent = []

    def create(**kwargs):
        sent.append(kwargs)
        return SyncStream(_openai_chunks())

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_calls=5)
    instrument._patch_openai_instance(client, Tracer(sink=Sink()), guard)
    list(client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        stream_options={"include_usage": False},
    ))
    assert sent[0]["stream_options"]["include_usage"] is False
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 200


def test_empty_stream_counts_one_call_zero_tokens():
    def create(**kwargs):
        return SyncStream([])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    instrument._patch_openai_instance(client, Tracer(sink=Sink()), guard)
    list(client.chat.completions.create(model="gpt-4o-mini", stream=True))
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 0
    assert guard.state.cost_used == 0.0


def test_aborted_stream_counts_one_call_zero_tokens():
    class Boom:
        usage = None

        def __iter__(self):
            yield SimpleNamespace(usage=None)
            raise RuntimeError("abort")

    def create(**kwargs):
        return Boom()

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    instrument._patch_openai_instance(client, Tracer(sink=Sink()), guard)
    with pytest.raises(RuntimeError, match="abort"):
        list(client.chat.completions.create(model="gpt-4o-mini", stream=True))
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 0
    assert guard.state.cost_used == 0.0


def test_nonstream_openai_still_bills_once():
    def create(**kwargs):
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    instrument._patch_openai_instance(client, Tracer(sink=Sink()), guard)
    client.chat.completions.create(model="gpt-4o-mini")
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15


def test_exhausted_budget_blocks_stream_before_dispatch():
    sent = []

    def create(**kwargs):
        sent.append(kwargs)
        return SyncStream(_openai_chunks())

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_calls=1)
    guard.consume(calls=1)
    sink = Sink()
    instrument._patch_openai_instance(client, Tracer(sink=sink), guard)
    with pytest.raises(BudgetExceeded):
        client.chat.completions.create(model="gpt-4o-mini", stream=True)
    assert sent == []
    assert any(e.get("name") == "guard.budget_exceeded" for e in sink.events)


def test_anthropic_create_stream_bills_final_chunk_once():
    usage = SimpleNamespace(input_tokens=80, output_tokens=40)

    def create(**kwargs):
        return SyncStream([
            SimpleNamespace(type="content", usage=None),
            SimpleNamespace(type="message_delta", usage=usage),
        ])

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    instrument._patch_anthropic_instance(client, Tracer(sink=Sink()), guard)
    list(client.messages.create(model="claude-sonnet-4-20250514", stream=True))
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 120


def test_anthropic_messages_stream_bills_get_final_message_once():
    message = _anthropic_message()

    def stream(**kwargs):
        return StreamManager(MessageStream(message))

    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **k: None, stream=stream))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    instrument._patch_anthropic_instance(client, Tracer(sink=Sink()), guard)
    with client.messages.stream(model="claude-sonnet-4-20250514") as body:
        final = body.get_final_message()
    assert final is message
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 120


def test_async_openai_stream_bills_once():
    sent = []

    async def create(**kwargs):
        sent.append(kwargs)
        return AsyncStream(_openai_chunks())

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)

    async def body():
        instrument._patch_openai_async_instance(client, AsyncTracer(sink=Sink()), guard)
        stream = await client.chat.completions.create(model="gpt-4o-mini", stream=True)
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        return len(chunks)

    assert asyncio.run(body()) == 3
    assert sent[0]["stream_options"]["include_usage"] is True
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 200


def test_async_anthropic_stream_manager_bills_once():
    message = _anthropic_message()

    def stream(**kwargs):
        return AsyncStreamManager(AsyncMessageStream(message))

    async def create(**kwargs):
        return SimpleNamespace(usage=message.usage)

    client = SimpleNamespace(messages=SimpleNamespace(create=create, stream=stream))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)

    async def body():
        instrument._patch_anthropic_async_instance(client, AsyncTracer(sink=Sink()), guard)
        async with client.messages.stream(model="claude-sonnet-4-20250514") as body_stream:
            return await body_stream.get_final_message()

    assert asyncio.run(body()) is message
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 120


def test_async_anthropic_create_stream_bills_once():
    usage = SimpleNamespace(input_tokens=11, output_tokens=9)

    async def create(**kwargs):
        return AsyncStream([
            SimpleNamespace(type="content", usage=None),
            SimpleNamespace(type="message_delta", usage=usage),
        ])

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)

    async def body():
        instrument._patch_anthropic_async_instance(client, AsyncTracer(sink=Sink()), guard)
        stream = await client.messages.create(model="claude-sonnet-4-20250514", stream=True)
        async for _chunk in stream:
            pass

    asyncio.run(body())
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 20
