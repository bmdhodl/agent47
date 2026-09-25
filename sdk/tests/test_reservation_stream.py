"""AG-05: store-backed streams reserve before send and settle once."""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentguard import AsyncTracer, BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer
from agentguard._reservation_contract import MissingBound, ReservationContractError
from agentguard._reservation_stream import settle_stream_reservation
from agentguard.instrument import _patch_anthropic_async_instance, _traced_openai_create
from agentguard.instrument_stream import run_traced_create, run_traced_create_async
from agentguard.precision_cost import SOURCE_OVERESTIMATE, SOURCE_ZERO, get_default_prices

ROOT = Path(__file__).resolve().parents[2]


class _Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class _SyncStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __iter__(self):
        return iter(self._chunks)


class _AsyncStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for chunk in self._chunks:
            yield chunk


class _AsyncMessage:
    def __init__(self, message):
        self._message = message

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        yield SimpleNamespace(type="delta", usage=None)

    async def get_final_message(self):
        return self._message


class _AsyncManager:
    def __init__(self, stream):
        self._stream = stream

    async def __aenter__(self):
        return self._stream

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _guard(tmp_path, **limits):
    options = {
        "max_calls": 1,
        "store": JsonFileStateStore(tmp_path / "budget.json"),
        "key": "fleet",
    }
    options.update(limits)
    return BudgetGuard(**options)


def _tracer():
    return Tracer(sink=_Sink(), watermark=False)


def _usage_chunks(prompt=120, completion=80):
    usage = SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
    )
    return [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="a"))], usage=None),
        SimpleNamespace(choices=[], usage=usage),
    ]


def _reasons(guard):
    state = guard._store.read(guard._period_bucket()) or {}
    return {
        key: rec.get("unresolved_reason")
        for key, rec in (state.get("reservations") or {}).items()
    }


def _patch_and_stream(guard, create, **kwargs):
    from agentguard.instrument import _patch_openai_instance

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    _patch_openai_instance(client, _tracer(), guard)
    options = {"model": "gpt-4o-mini", "stream": True}
    options.update(kwargs)
    return client.chat.completions.create(**options)


def test_two_store_streams_dispatch_once(tmp_path):
    store = JsonFileStateStore(tmp_path / "budget.json")
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    sent = []
    results = []

    def create(**_kwargs):
        with lock:
            sent.append(1)
        return _SyncStream(_usage_chunks())

    def worker():
        guard = BudgetGuard(max_calls=1, store=store, key="fleet")
        barrier.wait(5)
        try:
            stream = _traced_openai_create(
                create, _tracer(), guard, model="gpt-4o-mini", stream=True
            )
            list(stream)
        except BudgetExceeded:
            with lock:
                results.append("blocked")
        else:
            with lock:
                results.append("ok")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert sorted(results) == ["blocked", "ok"]
    assert sent == [1]
    totals = BudgetGuard(max_calls=1, store=store, key="fleet").reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["reserved"]["calls"] == 0
    assert totals["settled"]["tokens"] == 200


def test_in_memory_stream_still_consumes_after_the_fact():
    sent = []

    def create(**_kwargs):
        sent.append(1)
        return _SyncStream([])

    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    list(_patch_and_stream(guard, create))
    assert sent == [1]
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 0
    assert guard.reservation_totals()["reserved"]["calls"] == 0


def test_connection_error_keeps_unresolved_hold(tmp_path):
    guard = _guard(tmp_path)
    sent = []

    def create(**_kwargs):
        sent.append(1)
        raise ConnectionError("dropped")

    with pytest.raises(ConnectionError):
        _traced_openai_create(create, _tracer(), guard, model="gpt-4o-mini", stream=True)
    assert sent == [1]
    totals = guard.reservation_totals()
    assert totals["unresolved"]["calls"] == 1
    assert totals["settled"]["calls"] == 0
    assert set(_reasons(guard).values()) == {"provider_outcome_unknown"}
    with pytest.raises(BudgetExceeded):
        _traced_openai_create(create, _tracer(), guard, model="gpt-4o-mini", stream=True)
    assert sent == [1]


def test_late_usage_can_settle_an_unresolved_hold(tmp_path):
    guard = _guard(tmp_path)

    def create(**_kwargs):
        raise ConnectionError("dropped")

    with pytest.raises(ConnectionError):
        _traced_openai_create(create, _tracer(), guard, model="gpt-4o-mini", stream=True)
    reservation_id = guard.reservation_totals()["reservation_ids"]["unresolved"][0]
    guard.commit_reservation(reservation_id, tokens=4, cost_usd=0.0, calls=1)
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["unresolved"]["calls"] == 0
    assert totals["settled"]["tokens"] == 4


def test_timeout_before_dispatch_cancels_and_does_not_send(tmp_path):
    guard = _guard(tmp_path)
    sent = []

    def create(**_kwargs):
        sent.append(1)
        return _SyncStream(_usage_chunks())

    def abort():
        raise TimeoutError("local deadline")

    with pytest.raises(TimeoutError):
        run_traced_create(
            create,
            _tracer(),
            guard,
            "openai",
            (),
            {"model": "gpt-4o-mini", "stream": True},
            wrap_stream=True,
            check_budget=lambda *_a, **_k: None,
            emit_result=lambda *_a, **_k: None,
            consume_budget=lambda *_a, **_k: None,
            before_send=abort,
        )
    assert sent == []
    assert guard.reservation_totals()["reserved"]["calls"] == 0
    stream = _traced_openai_create(
        create, _tracer(), guard, model="gpt-4o-mini", stream=True
    )
    list(stream)
    assert sent == [1]
    assert guard.reservation_totals()["settled"]["calls"] == 1


def test_timeout_after_dispatch_keeps_the_hold(tmp_path):
    guard = _guard(tmp_path)

    def create(**_kwargs):
        raise TimeoutError("provider timed out")

    with pytest.raises(TimeoutError):
        _traced_openai_create(create, _tracer(), guard, model="gpt-4o-mini", stream=True)
    assert set(_reasons(guard).values()) == {"timeout"}
    with pytest.raises(BudgetExceeded):
        _traced_openai_create(
            lambda **_k: _SyncStream([]),
            _tracer(),
            guard,
            model="gpt-4o-mini",
            stream=True,
        )


def test_mid_stream_timeout_without_usage_stays_unresolved(tmp_path):
    guard = _guard(tmp_path, max_tokens=100)

    class Boom:
        def __iter__(self):
            yield SimpleNamespace(usage=None)
            raise TimeoutError("mid-stream")

    def create(**_kwargs):
        return Boom()

    with pytest.raises(TimeoutError):
        list(_patch_and_stream(guard, create, max_tokens=40))
    totals = guard.reservation_totals()
    assert totals["unresolved"]["calls"] == 1
    assert totals["settled"]["tokens"] == 0
    assert totals["unresolved"]["tokens"] == 40
    assert set(_reasons(guard).values()) == {"timeout"}


def test_partial_usage_then_error_does_not_commit(tmp_path):
    guard = _guard(tmp_path, max_tokens=1000)
    from agentguard.instrument import _patch_anthropic_instance

    class Body:
        def __iter__(self):
            yield SimpleNamespace(usage=SimpleNamespace(input_tokens=50, output_tokens=1))
            raise ConnectionError("dropped after message_start")

    class Manager:
        def __enter__(self):
            return Body()

        def __exit__(self, exc_type, exc, tb):
            return False

    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_k: None, stream=lambda **_k: Manager())
    )
    _patch_anthropic_instance(client, _tracer(), guard)
    with pytest.raises(ConnectionError), client.messages.stream(
        model="claude-sonnet-4-20250514", max_tokens=400
    ) as stream:
        list(stream)
    totals = guard.reservation_totals()
    assert totals["settled"]["tokens"] == 0
    assert totals["settled"]["calls"] == 0
    assert totals["unresolved"]["calls"] == 1
    assert totals["unresolved"]["tokens"] == 400
    assert set(_reasons(guard).values()) == {"provider_outcome_unknown"}


def test_partial_usage_then_close_keeps_the_token_hold(tmp_path):
    guard = _guard(tmp_path, max_tokens=1000)
    from agentguard.instrument import _patch_anthropic_instance

    class Body:
        def __iter__(self):
            yield SimpleNamespace(usage=SimpleNamespace(input_tokens=50, output_tokens=1))

    class Manager:
        def __enter__(self):
            return Body()

        def __exit__(self, exc_type, exc, tb):
            return False

    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_k: None, stream=lambda **_k: Manager())
    )
    _patch_anthropic_instance(client, _tracer(), guard)
    with client.messages.stream(model="claude-sonnet-4-20250514", max_tokens=400) as stream:
        next(stream)
    totals = guard.reservation_totals()
    assert totals["settled"]["tokens"] == 0
    assert totals["unresolved"]["tokens"] == 400
    assert set(_reasons(guard).values()) == {"stream_incomplete"}


def test_stream_enter_timeout_is_unresolved_not_reserved(tmp_path):
    guard = _guard(tmp_path, max_tokens=100)

    class Manager:
        def __enter__(self):
            raise TimeoutError("send failed")

        def __exit__(self, exc_type, exc, tb):
            return False

    from agentguard.instrument import _patch_anthropic_instance

    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_k: None, stream=lambda **_k: Manager())
    )
    _patch_anthropic_instance(client, _tracer(), guard)
    with pytest.raises(TimeoutError), client.messages.stream(
        model="claude-sonnet-4-20250514", max_tokens=40
    ):
        pass
    totals = guard.reservation_totals()
    assert totals["reserved"]["calls"] == 0
    assert totals["unresolved"]["calls"] == 1
    assert totals["unresolved"]["tokens"] == 40
    assert totals["settled"]["tokens"] == 0
    assert set(_reasons(guard).values()) == {"timeout"}


def test_unentered_stream_manager_stays_reserved(tmp_path):
    guard = _guard(tmp_path, max_calls=1)
    from agentguard.instrument import _patch_anthropic_instance

    class Manager:
        def __enter__(self):
            raise AssertionError("enter must not run")

        def __exit__(self, exc_type, exc, tb):
            return False

    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_k: None, stream=lambda **_k: Manager())
    )
    _patch_anthropic_instance(client, _tracer(), guard)
    client.messages.stream(model="claude-sonnet-4-20250514")
    totals = guard.reservation_totals()
    assert totals["reserved"]["calls"] == 1
    assert totals["unresolved"]["calls"] == 0
    assert totals["settled"]["calls"] == 0


def test_close_before_chunks_under_token_cap_stays_unresolved(tmp_path):
    guard = _guard(tmp_path, max_tokens=100)
    stream = _patch_and_stream(
        guard,
        lambda **_kwargs: _SyncStream(_usage_chunks()),
        max_tokens=40,
    )
    stream.close()
    totals = guard.reservation_totals()
    assert totals["settled"]["tokens"] == 0
    assert totals["unresolved"]["tokens"] == 40
    assert set(_reasons(guard).values()) == {"usage_missing"}


def test_calls_only_early_close_still_settles_one_call(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    stream = _patch_and_stream(guard, lambda **_kwargs: _SyncStream([]))
    stream.close()
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 0
    assert totals["unresolved"]["calls"] == 0


def test_async_stream_enter_timeout_is_unresolved(tmp_path):
    guard = _guard(tmp_path, max_tokens=100)

    class Manager:
        async def __aenter__(self):
            raise TimeoutError("send failed")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_k: None, stream=lambda **_k: Manager())
    )

    async def body():
        _patch_anthropic_async_instance(client, AsyncTracer(sink=_Sink()), guard)
        with pytest.raises(TimeoutError):
            async with client.messages.stream(
                model="claude-sonnet-4-20250514", max_tokens=40
            ):
                pass

    asyncio.run(body())
    totals = guard.reservation_totals()
    assert totals["reserved"]["calls"] == 0
    assert totals["unresolved"]["calls"] == 1
    assert totals["unresolved"]["tokens"] == 40
    assert set(_reasons(guard).values()) == {"timeout"}


def test_missing_usage_under_dollar_cap_is_not_authoritative_zero(tmp_path):
    guard = _guard(tmp_path, max_calls=2, max_cost_usd=1.0)

    def create(**_kwargs):
        return _SyncStream([])

    list(_patch_and_stream(guard, create, max_tokens=100))
    totals = guard.reservation_totals()
    assert totals["settled"]["cost"] == 0.0
    assert totals["settled"]["calls"] == 0
    assert totals["unresolved"]["calls"] == 1
    assert totals["unresolved"]["cost"] > 0
    assert set(_reasons(guard).values()) == {"usage_missing"}


def test_calls_only_missing_usage_settles_one_call(tmp_path):
    guard = _guard(tmp_path, max_calls=2)

    def create(**_kwargs):
        return _SyncStream([])

    list(_patch_and_stream(guard, create))
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 0
    assert totals["settled"]["cost"] == 0.0
    assert totals["unresolved"]["calls"] == 0


def test_final_usage_is_billed_once_including_close(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    sink = _Sink()

    def create(**kwargs):
        assert kwargs["stream_options"]["include_usage"] is True
        return _SyncStream(_usage_chunks())

    from agentguard.instrument import _patch_openai_instance

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    _patch_openai_instance(client, Tracer(sink=sink, watermark=False), guard)
    stream = client.chat.completions.create(model="gpt-4o-mini", stream=True)
    assert len(list(stream)) == 2
    stream.close()
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 200
    results = [event for event in sink.events if event.get("name") == "llm.result"]
    assert len(results) == 1
    assert results[0]["data"]["source_of_cost"] == "computed"


def test_duplicate_settle_does_not_double_count(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})
    usage = {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
    ctx = _tracer().trace("llm.openai.gpt-4o-mini").__enter__()
    settle_stream_reservation(
        guard, ctx, reservation_id, "gpt-4o-mini", "openai", usage, None
    )
    settle_stream_reservation(
        guard, ctx, reservation_id, "gpt-4o-mini", "openai", usage, None
    )
    assert guard.reservation_totals()["settled"]["calls"] == 1
    assert guard.reservation_totals()["settled"]["tokens"] == 5
    with pytest.raises(ReservationContractError):
        settle_stream_reservation(
            guard,
            ctx,
            reservation_id,
            "gpt-4o-mini",
            "openai",
            {"prompt_tokens": 9, "completion_tokens": 1, "total_tokens": 10},
            None,
        )
    assert guard.reservation_totals()["settled"]["calls"] == 1


def test_alias_model_uses_canonical_rate_once(tmp_path):
    guard = _guard(tmp_path, max_calls=2)

    def create(**_kwargs):
        return _SyncStream(_usage_chunks())

    list(_patch_and_stream(guard, create, model="gpt-4o-2024-08-06"))
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 200
    assert totals["settled"]["cost"] == pytest.approx(120 * 2.50 / 1_000_000 + 80 * 10.00 / 1_000_000)


def test_unknown_model_cost_is_overestimate_not_free(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    sink = _Sink()

    def create(**_kwargs):
        return _SyncStream(_usage_chunks())

    from agentguard.instrument import _patch_openai_instance

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    _patch_openai_instance(client, Tracer(sink=sink, watermark=False), guard)
    list(client.chat.completions.create(model="not-a-real-model", stream=True))
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["cost"] == pytest.approx(200 * 150.0 / 1_000_000)
    assert totals["settled"]["cost"] > 0
    results = [event for event in sink.events if event.get("name") == "llm.result"]
    assert results[-1]["data"]["source_of_cost"] == SOURCE_OVERESTIMATE


def test_missing_usage_fields_do_not_settle_authoritative_zero(tmp_path):
    guard = _guard(tmp_path, max_calls=2, max_cost_usd=5.0)
    sink = _Sink()

    def create(**_kwargs):
        return _SyncStream([SimpleNamespace(usage=SimpleNamespace())])

    from agentguard.instrument import _patch_openai_instance

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    _patch_openai_instance(client, Tracer(sink=sink, watermark=False), guard)
    list(client.chat.completions.create(model="gpt-4o-mini", stream=True, max_tokens=50))
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["cost"] > 0
    results = [event for event in sink.events if event.get("name") == "llm.result"]
    assert results[-1]["data"]["source_of_cost"] == SOURCE_OVERESTIMATE


def test_cache_tokens_are_not_double_counted(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "total_tokens": 110,
        "prompt_tokens_details": {"cached_tokens": 40},
    }
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})
    ctx = _tracer().trace("span").__enter__()
    settle_stream_reservation(
        guard, ctx, reservation_id, "gpt-4o-mini", "openai", usage, None
    )
    expected = (60 * 0.15 + 40 * 0.075 + 10 * 0.60) / 1_000_000
    doubled = (100 * 0.15 + 40 * 0.075 + 10 * 0.60) / 1_000_000
    assert guard.reservation_totals()["settled"]["cost"] == pytest.approx(expected)
    assert guard.reservation_totals()["settled"]["cost"] != pytest.approx(doubled)


def test_user_price_override_replaces_the_owned_table(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    prices = get_default_prices()
    prices["rates"][("openai", "gpt-4o-mini")] = {
        "input_per_1m": 100.0,
        "output_per_1m": 100.0,
    }
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})
    usage = {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}
    ctx = _tracer().trace("span").__enter__()
    settle_stream_reservation(
        guard, ctx, reservation_id, "gpt-4o-mini", "openai", usage, None, prices=prices
    )
    assert guard.reservation_totals()["settled"]["cost"] == pytest.approx(200 * 100.0 / 1_000_000)


def test_explicit_free_model_can_settle_zero(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "llama3.1"})
    usage = {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14}
    ctx = _tracer().trace("span").__enter__()
    settle_stream_reservation(
        guard, ctx, reservation_id, "llama3.1", "ollama", usage, None
    )
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["cost"] == 0.0
    assert totals["unresolved"]["calls"] == 0


def test_zero_non_free_cost_stays_unresolved(tmp_path, monkeypatch):
    guard = _guard(tmp_path, max_calls=2)

    def fake_resolve(*_args, **_kwargs):
        return {
            "cost_usd": 0.0,
            "tokens": {"total": 10, "input": 10, "output": 0},
            "source": "computed",
            "breakdown": {},
        }

    monkeypatch.setattr(
        "agentguard.precision_cost.resolve_billable_cost", fake_resolve
    )
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})
    ctx = _tracer().trace("span").__enter__()
    settle_stream_reservation(
        guard,
        ctx,
        reservation_id,
        "gpt-4o-mini",
        "openai",
        {"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
        None,
    )
    assert guard.reservation_totals()["settled"]["calls"] == 0
    assert set(_reasons(guard).values()) == {"cost_unresolved"}


def test_application_retry_is_a_second_reservation(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    calls = []

    def fail_then_ok(**_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionError("retry me")
        return _SyncStream(_usage_chunks(prompt=3, completion=2))

    with pytest.raises(ConnectionError):
        _traced_openai_create(fail_then_ok, _tracer(), guard, model="gpt-4o-mini", stream=True)
    list(
        _traced_openai_create(
            fail_then_ok, _tracer(), guard, model="gpt-4o-mini", stream=True
        )
    )
    totals = guard.reservation_totals()
    assert calls == [1, 1]
    assert totals["unresolved"]["calls"] == 1
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 5


def test_provider_retry_inside_one_create_is_one_hold(tmp_path):
    guard = _guard(tmp_path, max_calls=1)
    attempts = []

    def create(**_kwargs):
        attempts.append(1)
        attempts.append(1)
        return _SyncStream(_usage_chunks(prompt=1, completion=1))

    list(_patch_and_stream(guard, create))
    assert attempts == [1, 1]
    assert guard.reservation_totals()["settled"]["calls"] == 1


def test_missing_bound_does_not_send(tmp_path):
    guard = _guard(tmp_path, max_tokens=100)
    sent = []

    def create(**_kwargs):
        sent.append(1)
        return _SyncStream(_usage_chunks())

    with pytest.raises(MissingBound):
        _patch_and_stream(guard, create)
    assert sent == []
    assert guard.reservation_totals()["reserved"]["calls"] == 0


def test_async_stream_bills_once_and_blocks_the_next(tmp_path):
    store = JsonFileStateStore(tmp_path / "budget.json")
    sent = []

    async def create(**_kwargs):
        sent.append(1)
        return _AsyncStream(_usage_chunks())

    async def body():
        guard = BudgetGuard(max_calls=1, store=store, key="fleet")
        tracer = AsyncTracer(sink=_Sink())
        stream = await run_traced_create_async(
            create,
            tracer,
            guard,
            "openai",
            (),
            {"model": "gpt-4o-mini", "stream": True},
            wrap_stream=True,
            check_budget=lambda *_a, **_k: None,
            emit_result=lambda *_a, **_k: None,
            consume_budget=lambda *_a, **_k: None,
        )
        async for _chunk in stream:
            pass
        with pytest.raises(BudgetExceeded):
            await run_traced_create_async(
                create,
                tracer,
                guard,
                "openai",
                (),
                {"model": "gpt-4o-mini", "stream": True},
                wrap_stream=True,
                check_budget=lambda *_a, **_k: None,
                emit_result=lambda *_a, **_k: None,
                consume_budget=lambda *_a, **_k: None,
            )

    asyncio.run(body())
    assert sent == [1]
    totals = BudgetGuard(max_calls=1, store=store, key="fleet").reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 200


def test_async_connection_error_stays_unresolved(tmp_path):
    guard = _guard(tmp_path)

    async def create(**_kwargs):
        raise ConnectionError("async drop")

    async def body():
        tracer = AsyncTracer(sink=_Sink())
        with pytest.raises(ConnectionError):
            await run_traced_create_async(
                create,
                tracer,
                guard,
                "openai",
                (),
                {"model": "gpt-4o-mini", "stream": True},
                wrap_stream=True,
                check_budget=lambda *_a, **_k: None,
                emit_result=lambda *_a, **_k: None,
                consume_budget=lambda *_a, **_k: None,
            )

    asyncio.run(body())
    assert guard.reservation_totals()["unresolved"]["calls"] == 1
    assert set(_reasons(guard).values()) == {"provider_outcome_unknown"}


def test_async_anthropic_stream_reserves_on_enter(tmp_path):
    store = JsonFileStateStore(tmp_path / "budget.json")
    entered = []
    message = SimpleNamespace(
        usage=SimpleNamespace(input_tokens=80, output_tokens=40)
    )

    def stream(**_kwargs):
        entered.append(1)
        return _AsyncManager(_AsyncMessage(message))

    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **_k: None, stream=stream))
    guard = BudgetGuard(max_calls=1, store=store, key="fleet")

    async def body():
        _patch_anthropic_async_instance(client, AsyncTracer(sink=_Sink()), guard)
        pending = client.messages.stream(model="claude-sonnet-4-20250514")
        assert entered == []
        assert guard.reservation_totals()["reserved"]["calls"] == 0
        async with pending as body_stream:
            final = await body_stream.get_final_message()
        assert final is message
        with pytest.raises(BudgetExceeded):
            async with client.messages.stream(model="claude-sonnet-4-20250514"):
                pass

    asyncio.run(body())
    assert entered == [1]
    totals = BudgetGuard(max_calls=1, store=store, key="fleet").reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 120


def test_async_anthropic_timeout_on_enter_keeps_the_hold(tmp_path):
    guard = _guard(tmp_path)

    def stream(**_kwargs):
        raise TimeoutError("connect")

    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **_k: None, stream=stream))

    async def body():
        _patch_anthropic_async_instance(client, AsyncTracer(sink=_Sink()), guard)
        with pytest.raises(TimeoutError):
            async with client.messages.stream(model="claude-sonnet-4-20250514"):
                pass

    asyncio.run(body())
    assert set(_reasons(guard).values()) == {"timeout"}
    assert guard.reservation_totals()["unresolved"]["calls"] == 1


def test_response_usage_is_used_when_the_stream_did_not_capture_it(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    from agentguard._reservation_stream import begin_stream_reservation

    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})
    ctx = _tracer().trace("span").__enter__()
    settle_stream_reservation(
        guard,
        ctx,
        reservation_id,
        "gpt-4o-mini",
        "openai",
        None,
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
    )
    assert guard.reservation_totals()["settled"]["tokens"] == 2


def test_unresolvable_cost_keeps_the_hold(tmp_path, monkeypatch):
    from agentguard._reservation_stream import begin_stream_reservation
    from agentguard.precision_cost import CostResolutionError

    guard = _guard(tmp_path, max_calls=2)
    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})

    def fail(*_args, **_kwargs):
        raise CostResolutionError("strict")

    monkeypatch.setattr("agentguard.precision_cost.resolve_billable_cost", fail)
    ctx = _tracer().trace("span").__enter__()
    with pytest.raises(CostResolutionError):
        settle_stream_reservation(
            guard,
            ctx,
            reservation_id,
            "gpt-4o-mini",
            "openai",
            {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            None,
        )
    assert set(_reasons(guard).values()) == {"cost_unresolved"}
    assert guard.reservation_totals()["settled"]["calls"] == 0


def test_commit_failure_keeps_the_hold(tmp_path):
    from agentguard._reservation_stream import begin_stream_reservation

    guard = _guard(tmp_path, max_calls=2)
    reservation_id = begin_stream_reservation(guard, {"model": "gpt-4o-mini"})

    def fail(*_args, **_kwargs):
        raise RuntimeError("store write failed")

    guard.commit_reservation = fail
    ctx = _tracer().trace("span").__enter__()
    with pytest.raises(RuntimeError):
        settle_stream_reservation(
            guard,
            ctx,
            reservation_id,
            "gpt-4o-mini",
            "openai",
            {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            None,
        )
    assert set(_reasons(guard).values()) == {"settlement_failed"}


def test_stream_module_is_not_a_public_export():
    import agentguard

    assert "_reservation_stream" not in agentguard.__all__
    assert "settle_stream_reservation" not in agentguard.__all__
    assert SOURCE_ZERO == "zero"


@pytest.mark.integration
def test_stream_reservation_runs_from_installed_distribution(tmp_path):
    target = tmp_path / "site-packages"
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            str(ROOT / "sdk"),
            "--target",
            str(target),
            "--no-deps",
            "--disable-pip-version-check",
        ],
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr or install.stdout
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    env.pop("PYTHONHOME", None)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import pathlib, agentguard\n"
                "from agentguard import BudgetGuard, JsonFileStateStore, Tracer\n"
                "from agentguard.instrument import _traced_openai_create\n"
                "from types import SimpleNamespace\n"
                "assert 'settle_stream_reservation' not in agentguard.__all__\n"
                "class Drop:\n"
                "    def emit(self, _event):\n"
                "        return None\n"
                "class Stream:\n"
                "    def __iter__(self):\n"
                "        usage = SimpleNamespace(prompt_tokens=2, completion_tokens=2, total_tokens=4)\n"
                "        yield SimpleNamespace(usage=usage)\n"
                "store = JsonFileStateStore(pathlib.Path('budget.json'))\n"
                "guard = BudgetGuard(max_calls=1, store=store, key='fleet')\n"
                "def create(**_kwargs):\n"
                "    return Stream()\n"
                "list(_traced_openai_create(create, Tracer(sink=Drop(), watermark=False), guard, model='gpt-4o-mini', stream=True))\n"
                "totals = guard.reservation_totals()\n"
                "assert totals['settled']['calls'] == 1, totals\n"
                "assert totals['settled']['tokens'] == 4, totals\n"
                "print(pathlib.Path(agentguard.__file__).resolve())\n"
                "print('HELD')\n"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    installed = Path(lines[0]).resolve()
    assert lines[1] == "HELD"
    assert target.resolve() in installed.parents
