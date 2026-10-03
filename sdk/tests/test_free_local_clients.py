"""Real OpenAI clients: explicit free billing must preserve paid calls and limits."""
from __future__ import annotations

import asyncio
import gc
import inspect
import json
import sys
import types
import weakref

import pytest
from test_real_dispatch import (
    OPENAI_COMPLETION,
    OPENAI_RESPONSE,
    _chat_sse,
    _CountingTransport,
    _has_responses,
    _require,
    _sse,
)

import agentguard
from agentguard import (
    AsyncTracer,
    BudgetExceeded,
    BudgetGuard,
    JsonFileStateStore,
    JsonlFileSink,
    Tracer,
)
from agentguard.cli import _report
from agentguard.instrument import (
    patch_openai,
    patch_openai_async,
    unpatch_openai_async,
)
from agentguard.reporting import render_incident_report


@pytest.fixture
def sdk():
    agentguard.shutdown()
    yield _require("openai")
    agentguard.shutdown()


def _client(sdk, transport, asynchronous=False):
    cls = sdk.AsyncOpenAI if asynchronous else sdk.OpenAI
    http = sdk.DefaultAsyncHttpxClient if asynchronous else sdk.DefaultHttpxClient
    return cls(api_key="offline-test", base_url="http://127.0.0.1:11434/v1", max_retries=0,
               http_client=http(transport=transport.transport))


def _request(client, api, streamed=False):
    kwargs = {"model": "unpriced-local-test", "stream": streamed}
    if api == "chat":
        return client.chat.completions.create, {**kwargs, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 15}
    return client.responses.create, {**kwargs, "input": "hi", "max_output_tokens": 15}


async def _async_call(method, kwargs):
    result = await method(**kwargs)
    if kwargs.get("stream"):
        async with result:
            return [chunk async for chunk in result]
    return result


def _sync_call(method, kwargs):
    result = method(**kwargs)
    if kwargs.get("stream"):
        with result:
            return list(result)
    return result


def _results(path):
    return [e for e in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if e["name"] == "llm.result"]


def _assert_free_report(path, capsys):
    _report(str(path), as_json=True)
    report = json.loads(capsys.readouterr().out)
    assert report["llm_results"] == 1
    assert report["estimated_cost_usd"] == 0
    assert json.loads(render_incident_report(str(path), output_format="json"))["cost_usd"] == 0


@pytest.mark.parametrize("api", ["chat", "responses"])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("streamed", [False, True], ids=["response", "stream"])
@pytest.mark.parametrize("stored", [False, True], ids=["memory", "store"])
def test_named_local_client_is_free_while_paid_client_and_limits_stay_active(sdk, tmp_path, capsys, api, asynchronous, streamed, stored):
    """REGRESSION: shared patches must bill only the explicitly named client free."""
    if api == "responses" and not _has_responses(sdk):
        pytest.skip("Responses needs OpenAI >=1.66")
    body = (_sse(OPENAI_RESPONSE) if api == "responses" else _chat_sse()) if streamed else (OPENAI_RESPONSE if api == "responses" else OPENAI_COMPLETION)
    local_transport = _CountingTransport(sdk, body)
    paid_transport = _CountingTransport(sdk, body)
    path = tmp_path / "traces.jsonl"
    guard = BudgetGuard(max_calls=2, max_tokens=30, max_cost_usd=.01,
                        **({"store": JsonFileStateStore(tmp_path / "budget.json"), "key": "mixed"} if stored else {}))
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=JsonlFileSink(str(path)))
    patch = patch_openai_async if asynchronous else patch_openai

    async def run_async():
        async with _client(sdk, local_transport, True) as local, _client(sdk, paid_transport, True) as paid:
            resource = local.responses if api == "responses" else local.chat.completions
            patch(tracer, budget_guard=guard, free_local_clients=[local])
            method, kwargs = _request(local, api, streamed)
            assert method.__self__ is resource
            await _async_call(method, kwargs)
            assert guard.state.cost_used == 0
            _assert_free_report(path, capsys)
            await _async_call(*_request(paid, api, streamed))
            with pytest.raises(BudgetExceeded):
                await _async_call(*_request(local, api, streamed))

    if asynchronous:
        asyncio.run(run_async())
    else:
        with _client(sdk, local_transport) as local, _client(sdk, paid_transport) as paid:
            # Cache the resource before activation; a saved bound method bypasses patches.
            resource = local.responses if api == "responses" else local.chat.completions
            patch(tracer, budget_guard=guard, free_local_clients=[local])
            method, kwargs = _request(local, api, streamed)
            assert method.__self__ is resource
            _sync_call(method, kwargs)
            assert guard.state.cost_used == 0
            _assert_free_report(path, capsys)
            _sync_call(*_request(paid, api, streamed))
            with pytest.raises(BudgetExceeded):
                _sync_call(*_request(local, api, streamed))

    results = _results(path)
    assert len(results) == 2
    assert results[0]["data"]["provider"] == "local"
    assert results[0]["data"]["source_of_cost"] == "zero"
    assert results[0]["cost_usd"] == 0
    assert results[1]["data"]["provider"] == "openai"
    assert results[1]["cost_usd"] > 0
    assert guard.state.cost_used == pytest.approx(results[1]["cost_usd"])
    assert guard.state.tokens_used == 30 and guard.state.calls_used == 2
    assert len(local_transport.requests) == len(paid_transport.requests) == 1
    if stored and (streamed or not asynchronous):
        totals = guard.reservation_totals()
        assert totals["settled"]["calls"] == 2
        assert totals["reserved"]["calls"] == totals["unresolved"]["calls"] == 0


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("streamed", [False, True])
def test_free_store_dollar_bound_does_not_need_an_output_bound(sdk, tmp_path, asynchronous, streamed):
    """A declared free call reserves zero dollars even without a token bound."""
    transport = _CountingTransport(sdk, _chat_sse() if streamed else OPENAI_COMPLETION)
    guard = BudgetGuard(max_calls=1, max_cost_usd=1e-12, store=JsonFileStateStore(tmp_path / "budget.json"), key="free")
    patch = patch_openai_async if asynchronous else patch_openai
    tracer = (AsyncTracer if asynchronous else Tracer)()
    kwargs = {"model": "free-model", "messages": [{"role": "user", "content": "hi"}], "stream": streamed}
    async def run():
        async with _client(sdk, transport, True) as client:
            patch(tracer, budget_guard=guard, free_local_clients=[client])
            await _async_call(client.chat.completions.create, kwargs)
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch(tracer, budget_guard=guard, free_local_clients=[client])
            _sync_call(client.chat.completions.create, kwargs)
    assert guard.state.cost_used == 0
    assert guard.state.calls_used == 1
    if streamed or not asynchronous:
        assert guard.reservation_totals()["settled"]["calls"] == 1


@pytest.mark.parametrize("bad", [None, "client", [object()]], ids=["none", "string", "object"])
def test_invalid_clients_do_not_activate_patch(sdk, bad):
    original = sdk.resources.chat.completions.Completions.create
    with pytest.raises(TypeError, match="free_local_clients"):
        patch_openai(Tracer(), free_local_clients=bad)
    assert sdk.resources.chat.completions.Completions.create is original


@pytest.mark.parametrize("asynchronous", [False, True])
def test_wrong_client_kind_does_not_activate_patch(sdk, asynchronous):
    transport = _CountingTransport(sdk, OPENAI_COMPLETION)
    wrong = _client(sdk, transport, not asynchronous)
    try:
        with pytest.raises(TypeError, match="free_local_clients"):
            (patch_openai_async if asynchronous else patch_openai)(Tracer(), free_local_clients=[wrong])
    finally:
        if asynchronous:
            wrong.close()
        else:
            asyncio.run(wrong.close())


def test_init_rejects_invalid_entries_before_creating_a_trace_file(sdk, tmp_path):
    path = tmp_path / "invalid.jsonl"
    original = sdk.resources.chat.completions.Completions.create
    with pytest.raises(TypeError, match="free_local_clients"):
        agentguard.init(local_only=True, trace_file=str(path), free_local_clients=[object()])
    assert not path.exists()
    assert sdk.resources.chat.completions.Completions.create is original
    assert agentguard.get_tracer() is None


def test_init_rejects_free_clients_when_auto_patch_is_disabled(sdk, tmp_path):
    with _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION)) as client, pytest.raises(ValueError, match="auto_patch"):
        agentguard.init(local_only=True, auto_patch=False, trace_file=str(tmp_path / "unused.jsonl"), free_local_clients=[client])


def test_free_client_requires_the_optional_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ImportError):
        patch_openai(Tracer(), free_local_clients=[object()])


def test_patch_does_not_keep_a_free_client_alive(sdk):
    client = _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION))
    ref = weakref.ref(client)
    patch_openai(Tracer(), free_local_clients=[client])
    client.close()
    del client
    gc.collect()
    assert ref() is None


def test_init_splits_sync_and_async_clients_and_shutdown_clears_free_policy(sdk, tmp_path):
    path = tmp_path / "init.jsonl"
    sync_transport = _CountingTransport(sdk, OPENAI_COMPLETION)
    async_transport = _CountingTransport(sdk, OPENAI_COMPLETION)
    async def run():
        with _client(sdk, sync_transport) as sync:
            async with _client(sdk, async_transport, True) as asynchronous:
                agentguard.init(local_only=True, trace_file=str(path), budget_usd=1e-6, free_local_clients=(c for c in [sync, asynchronous]))
                sync.chat.completions.create(model="local", messages=[])
                await asynchronous.chat.completions.create(model="local", messages=[])
                assert all(e["data"]["source_of_cost"] == "zero" for e in _results(path))
                agentguard.shutdown()
                guard = BudgetGuard(max_calls=1)
                patch_openai(Tracer(), budget_guard=guard)
                sync.chat.completions.create(model="local", messages=[])
                assert guard.state.cost_used > 0
    asyncio.run(run())


def test_repeated_patch_keeps_original_tracer_guard_and_client_policy(sdk, tmp_path):
    a = BudgetGuard(max_calls=10)
    b = BudgetGuard(max_calls=10)
    path_a, path_b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    with _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION)) as local, _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION)) as paid:
        patch_openai(Tracer(sink=JsonlFileSink(str(path_a))), budget_guard=a, free_local_clients=[local])
        patch_openai(Tracer(sink=JsonlFileSink(str(path_b))), budget_guard=b, free_local_clients=[paid])
        local.chat.completions.create(model="unknown", messages=[])
        paid.chat.completions.create(model="unknown", messages=[])
    assert a.state.calls_used == 2 and b.state.calls_used == 0
    assert _results(path_a)[0]["cost_usd"] == 0
    assert _results(path_a)[1]["cost_usd"] > 0
    assert not path_b.exists() or not path_b.read_text(encoding="utf-8")


@pytest.mark.parametrize("asynchronous", [False, True])
def test_responses_parse_keeps_declared_cost_zero(sdk, tmp_path, asynchronous):
    if not _has_responses(sdk):
        pytest.skip("Responses needs OpenAI >=1.66")
    path = tmp_path / "parse.jsonl"
    transport = _CountingTransport(sdk, OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=1)
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=JsonlFileSink(str(path)))
    async def run():
        async with _client(sdk, transport, True) as client:
            patch_openai_async(tracer, budget_guard=guard, free_local_clients=[client])
            await client.responses.parse(model="local", input="hi")
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch_openai(tracer, budget_guard=guard, free_local_clients=[client])
            client.responses.parse(model="local", input="hi")
    assert guard.state.tokens_used == 15 and guard.state.calls_used == 1
    assert guard.state.cost_used == _results(path)[0]["cost_usd"] == 0
    assert len(transport.requests) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("streamed", [False, True])
def test_raw_responses_account_once_for_named_client(sdk, tmp_path, asynchronous, streamed):
    if not _has_responses(sdk):
        pytest.skip("Responses needs OpenAI >=1.66")
    path = tmp_path / "raw.jsonl"
    transport = _CountingTransport(sdk, _sse(OPENAI_RESPONSE) if streamed else OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(tmp_path / "budget.json"), key="raw")
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=JsonlFileSink(str(path)))
    async def run():
        async with _client(sdk, transport, True) as client:
            patch_openai_async(tracer, budget_guard=guard, free_local_clients=[client])
            # Construct raw helpers after patching; old helpers retain old bound methods.
            raw = await client.responses.with_raw_response.create(model="local", input="hi", stream=streamed)
            result = raw.parse()
            if inspect.isawaitable(result):
                result = await result
            if streamed:
                async with result:
                    assert [event async for event in result][-1].type == "response.completed"
            else:
                assert result.usage.total_tokens == 15
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch_openai(tracer, budget_guard=guard, free_local_clients=[client])
            raw = client.responses.with_raw_response.create(model="local", input="hi", stream=streamed)
            result = raw.parse()
            if streamed:
                with result:
                    assert list(result)[-1].type == "response.completed"
            else:
                assert result.usage.total_tokens == 15
    assert len(_results(path)) == len(transport.requests) == 1
    assert guard.state.tokens_used == 15 and guard.state.calls_used == 1
    assert guard.state.cost_used == _results(path)[0]["cost_usd"] == 0


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("stored", [False, True])
def test_free_clients_still_refuse_an_exhausted_token_budget(sdk, tmp_path, asynchronous, stored):
    transport = _CountingTransport(sdk, OPENAI_COMPLETION)
    guard = BudgetGuard(max_tokens=0, **({"store": JsonFileStateStore(tmp_path / "budget.json"), "key": "tokens"} if stored else {}))
    async def run():
        async with _client(sdk, transport, True) as client:
            patch_openai_async(AsyncTracer(), budget_guard=guard, free_local_clients=[client])
            with pytest.raises(BudgetExceeded):
                await _async_call(*_request(client, "chat"))
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch_openai(Tracer(), budget_guard=guard, free_local_clients=[client])
            with pytest.raises(BudgetExceeded):
                _sync_call(*_request(client, "chat"))
    assert not transport.requests
    assert guard.state.cost_used == guard.state.calls_used == 0


def test_validation_checks_all_entries_before_patching(sdk):
    original = sdk.resources.chat.completions.Completions.create
    with _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION)) as client:
        with pytest.raises(TypeError, match="free_local_clients"):
            patch_openai(Tracer(), free_local_clients=[client, object()])
        assert sdk.resources.chat.completions.Completions.create is original


def test_non_weak_referenceable_clients_fail_before_patching(sdk, monkeypatch):
    class NonWeakClient:
        __slots__ = ()
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=NonWeakClient))
    original = sdk.resources.chat.completions.Completions.create
    with pytest.raises(TypeError, match="weak references"):
        patch_openai(Tracer(), free_local_clients=[NonWeakClient()])
    assert sdk.resources.chat.completions.Completions.create is original


def test_explicit_free_declaration_precedes_known_or_reported_price(sdk, tmp_path, monkeypatch):
    monkeypatch.setenv("STRICT_PRECISION", "1")
    transport = _CountingTransport(sdk, {**OPENAI_COMPLETION, "cost_usd": 100})
    path = tmp_path / "strict.jsonl"
    with _client(sdk, transport) as client:
        patch_openai(Tracer(sink=JsonlFileSink(str(path))), free_local_clients=[client])
        client.chat.completions.create(model="gpt-4o-mini", messages=[])
    assert _results(path)[0]["cost_usd"] == 0
    assert _results(path)[0]["data"]["source_of_cost"] == "zero"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_free_partial_stream_keeps_its_token_hold(sdk, tmp_path, asynchronous):
    path = tmp_path / "partial.jsonl"
    transport = _CountingTransport(sdk, _chat_sse())
    guard = BudgetGuard(max_tokens=15, max_calls=1, max_cost_usd=1e-12,
                        store=JsonFileStateStore(tmp_path / "budget.json"), key="partial")
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=JsonlFileSink(str(path)))
    async def run():
        async with _client(sdk, transport, True) as client:
            patch_openai_async(tracer, budget_guard=guard, free_local_clients=[client])
            stream = await client.chat.completions.create(**_request(client, "chat", True)[1])
            async with stream:
                await stream.__anext__()
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch_openai(tracer, budget_guard=guard, free_local_clients=[client])
            stream = client.chat.completions.create(**_request(client, "chat", True)[1])
            with stream:
                next(stream)
    totals = guard.reservation_totals()
    assert totals["unresolved"]["calls"] == 1
    assert totals["unresolved"]["tokens"] == 15
    assert totals["unresolved"]["cost"] == 0
    assert totals["settled"]["calls"] == 0
    assert _results(path)[0]["data"]["reason"] == "usage_missing"
    assert _results(path)[0]["cost_usd"] == 0


def test_async_repeated_patch_and_unpatch_restore_paid_defaults(sdk, tmp_path):
    path = tmp_path / "async-policy.jsonl"
    a, b = BudgetGuard(max_calls=10), BudgetGuard(max_calls=10)
    async def run():
        async with _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION), True) as local, _client(sdk, _CountingTransport(sdk, OPENAI_COMPLETION), True) as paid:
            patch_openai_async(AsyncTracer(sink=JsonlFileSink(str(path))), budget_guard=a, free_local_clients=[local])
            patch_openai_async(AsyncTracer(), budget_guard=b, free_local_clients=[paid])
            await local.chat.completions.create(model="local", messages=[])
            await paid.chat.completions.create(model="local", messages=[])
            assert a.state.calls_used == 2 and b.state.calls_used == 0
            assert _results(path)[0]["cost_usd"] == 0 < _results(path)[1]["cost_usd"]
            unpatch_openai_async()
            patch_openai_async(AsyncTracer(), budget_guard=b)
            await local.chat.completions.create(model="local", messages=[])
            assert b.state.cost_used > 0
    asyncio.run(run())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("cap", ["calls", "tokens", "dollars"])
def test_completed_free_stream_without_usage_records_zero_and_keeps_unknown_holds(sdk, tmp_path, capsys, asynchronous, cap):
    """REGRESSION: free billing also applies to the missing-usage settlement branch."""
    path = tmp_path / "missing-usage.jsonl"
    body = "\n".join(line for line in _chat_sse().split("\n") if '"usage"' not in line)
    transport = _CountingTransport(sdk, body)
    guard = BudgetGuard(max_calls=1,
                        **({"max_tokens": 15} if cap == "tokens" else {"max_cost_usd": 1e-12} if cap == "dollars" else {}),
                        store=JsonFileStateStore(tmp_path / "budget.json"), key="missing")
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=JsonlFileSink(str(path)))
    async def run():
        async with _client(sdk, transport, True) as client:
            patch_openai_async(tracer, budget_guard=guard, free_local_clients=[client])
            await _async_call(*_request(client, "chat", True))
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            patch_openai(tracer, budget_guard=guard, free_local_clients=[client])
            _sync_call(*_request(client, "chat", True))
    result = _results(path)[0]
    assert result["cost_usd"] == 0
    assert result["data"]["provider"] == "local"
    assert result["data"]["usage"] is None
    assert len(transport.requests) == 1
    totals = guard.reservation_totals()
    if cap == "calls":
        assert result["data"]["source_of_cost"] == "zero"
        assert totals["settled"]["calls"] == 1
        assert totals["unresolved"]["calls"] == 0
    else:
        assert result["data"]["reason"] == "usage_missing"
        assert totals["unresolved"]["calls"] == 1
        assert totals["unresolved"]["cost"] == 0
        assert totals["settled"]["calls"] == 0
    _assert_free_report(path, capsys)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_missing_standard_sdk_owner_refuses_free_configuration_before_activation(sdk, monkeypatch, asynchronous):
    """REGRESSION: an unsupported owner layout must not silently charge a named client."""
    original = getattr(sdk.resources.chat.completions, "AsyncCompletions" if asynchronous else "Completions").create
    transport = _CountingTransport(sdk, OPENAI_COMPLETION)
    async def run():
        async with _client(sdk, transport, True) as client:
            monkeypatch.delattr(client.chat.completions, "_client")
            with pytest.raises(TypeError, match=r"free_local_clients.*owner"):
                patch_openai_async(AsyncTracer(), free_local_clients=[client])
    if asynchronous:
        asyncio.run(run())
    else:
        with _client(sdk, transport) as client:
            monkeypatch.delattr(client.chat.completions, "_client")
            with pytest.raises(TypeError, match=r"free_local_clients.*owner"):
                patch_openai(Tracer(), free_local_clients=[client])
    current = getattr(sdk.resources.chat.completions, "AsyncCompletions" if asynchronous else "Completions").create
    assert current is original
    assert not transport.requests
