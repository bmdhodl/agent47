"""AG-07: guards against the real framework and provider packages.

Every other test uses stand-ins, so an upstream release that renames a hook
would pass CI while enforcement silently stopped. These tests import the real
packages. They skip when a package is missing, unless
``AGENTGUARD_REQUIRE_REAL_DEPS=1`` is set: the compat CI job sets it so a
missing package fails instead of skipping.

Provider tests send nothing over the network. The real SDK client runs its own
request pipeline into an ``httpx.MockTransport`` that counts dispatches.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

import pytest

from agentguard import (
    AsyncTracer,
    BudgetExceeded,
    BudgetGuard,
    JsonFileStateStore,
    JsonlFileSink,
    Tracer,
)
from agentguard.instrument import (
    patch_anthropic,
    patch_anthropic_async,
    patch_openai,
    patch_openai_async,
    unpatch_anthropic,
    unpatch_anthropic_async,
    unpatch_openai,
    unpatch_openai_async,
)


def _require(module: str) -> Any:
    if os.environ.get("AGENTGUARD_REQUIRE_REAL_DEPS") == "1":
        return importlib.import_module(module)
    return pytest.importorskip(module)


class _CountingTransport:
    """Mock transport, built from the httpx flavor the SDK itself uses."""

    def __init__(self, sdk: Any, body: Union[Dict[str, Any], str]) -> None:
        # anthropic 1.8 moved to httpx2 and rejects httpx objects, so take the
        # transport module from the SDK's own default client class.
        client_base = next(c for c in sdk.DefaultHttpxClient.__mro__ if c.__name__ == "Client")
        self._http = importlib.import_module(client_base.__module__.split(".")[0])
        self.requests: List[Any] = []
        self._body = body
        self.transport = self._http.MockTransport(self._handle)

    def _handle(self, request: Any) -> Any:
        self.requests.append(request)
        if isinstance(self._body, str):
            return self._http.Response(
                200, text=self._body, headers={"content-type": "text/event-stream"}
            )
        return self._http.Response(200, json=self._body)


OPENAI_COMPLETION = {
    "id": "chatcmpl-compat",
    "object": "chat.completion",
    "created": 0,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "ok"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

ANTHROPIC_MESSAGE = {
    "id": "msg_compat",
    "type": "message",
    "role": "assistant",
    "model": "claude-haiku-4-5-20251001",
    "content": [{"type": "text", "text": "ok"}],
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {"input_tokens": 10, "output_tokens": 5},
}


@pytest.fixture
def openai_sdk():
    yield _require("openai")
    unpatch_openai()
    unpatch_openai_async()


@pytest.fixture
def anthropic_sdk():
    yield _require("anthropic")
    unpatch_anthropic()
    unpatch_anthropic_async()


def _client(sdk: Any, client_cls: str, transport: _CountingTransport) -> Any:
    return getattr(sdk, client_cls)(
        api_key="sk-compat",
        max_retries=0,
        http_client=sdk.DefaultHttpxClient(transport=transport.transport),
    )


def test_openai_patch_stops_the_second_call_before_dispatch(openai_sdk):
    transport = _CountingTransport(openai_sdk, OPENAI_COMPLETION)
    guard = BudgetGuard(max_calls=1)
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(openai_sdk, "OpenAI", transport)
    messages = [{"role": "user", "content": "hi"}]

    client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    with pytest.raises(BudgetExceeded):
        client.chat.completions.create(model="gpt-4o-mini", messages=messages)

    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15


def test_openai_store_backed_reservation_dispatches_once(openai_sdk, tmp_path):
    transport = _CountingTransport(openai_sdk, OPENAI_COMPLETION)
    store = JsonFileStateStore(tmp_path / "budget.json")
    guard = BudgetGuard(max_calls=1, store=store, key="compat")
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(openai_sdk, "OpenAI", transport)
    messages = [{"role": "user", "content": "hi"}]

    client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    with pytest.raises(BudgetExceeded):
        client.chat.completions.create(model="gpt-4o-mini", messages=messages)

    assert len(transport.requests) == 1
    sent = json.loads(transport.requests[0].content)
    assert sent["model"] == "gpt-4o-mini"


def test_anthropic_patch_stops_the_second_call_before_dispatch(anthropic_sdk):
    transport = _CountingTransport(anthropic_sdk, ANTHROPIC_MESSAGE)
    guard = BudgetGuard(max_calls=1)
    patch_anthropic(Tracer(), budget_guard=guard)
    client = _client(anthropic_sdk, "Anthropic", transport)
    kwargs = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "hi"}],
    }

    client.messages.create(**kwargs)
    with pytest.raises(BudgetExceeded):
        client.messages.create(**kwargs)

    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15


def _chat_sse() -> str:
    base = {
        "id": "chatcmpl-compat", "object": "chat.completion.chunk",
        "created": 0, "model": "gpt-4o-mini",
    }
    chunks = [
        {**base, "choices": [{"index": 0, "delta": {"content": "ok"}, "finish_reason": None}]},
        {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        {**base, "choices": [], "usage": OPENAI_COMPLETION["usage"]},
    ]
    return "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"


def _anthropic_sse() -> str:
    message = {**ANTHROPIC_MESSAGE, "content": [], "stop_reason": None,
               "usage": {"input_tokens": 10, "output_tokens": 0}}
    events = [
        {"type": "message_start", "message": message},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ok"}},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
         "usage": {"output_tokens": 5}},
        {"type": "message_stop"},
    ]
    return "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events)


def _assert_billed_once(guard: BudgetGuard, path: Path, transport: _CountingTransport) -> None:
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    billing = [event for event in events if event["name"] == "llm.result"]
    assert len(billing) == 1
    assert billing[0]["cost_usd"] > 0
    assert guard.state.cost_used == pytest.approx(billing[0]["cost_usd"])


def _assert_stream_settled(guard: BudgetGuard) -> None:
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["reserved"]["calls"] == totals["unresolved"]["calls"] == 0


@pytest.mark.parametrize("api", ["chat", "responses"])
@pytest.mark.parametrize("resource_export", [True, False], ids=["reexported", "cached"])
def test_openai_existing_client_is_guarded(openai_sdk, tmp_path, monkeypatch, api, resource_export):
    """REGRESSION: a resource obtained before patching must enforce the budget."""
    if api == "responses" and not _has_responses(openai_sdk):
        pytest.skip("the Responses API needs openai>=1.66")
    body = OPENAI_RESPONSE if api == "responses" else OPENAI_COMPLETION
    kwargs = {"model": "gpt-4o-mini"}
    kwargs.update({"input": "hi"} if api == "responses" else {"messages": [{"role": "user", "content": "hi"}]})
    path = tmp_path / "early.jsonl"
    transport = _CountingTransport(openai_sdk, body)
    guard = BudgetGuard(max_calls=1)
    with _client(openai_sdk, "OpenAI", transport) as early:
        resource = early.responses if api == "responses" else early.chat.completions
        if not resource_export:
            # REGRESSION: cached resource submodules can outlive the root SDK
            # module, so a re-import need not restore openai.resources.
            monkeypatch.delattr(openai_sdk, "resources", raising=False)
        patch_openai(Tracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
        patch_openai(Tracer(), budget_guard=BudgetGuard(max_calls=0))
        resource.create(**kwargs)
        with _client(openai_sdk, "OpenAI", transport) as late:
            late_resource = late.responses if api == "responses" else late.chat.completions
            with pytest.raises(BudgetExceeded):
                late_resource.create(**kwargs)
        with pytest.raises(BudgetExceeded):
            resource.create(**kwargs)
    _assert_billed_once(guard, path, transport)


@pytest.mark.parametrize("api", ["chat", "responses"])
@pytest.mark.parametrize("resource_export", [True, False], ids=["reexported", "cached"])
def test_openai_existing_async_client_is_guarded(openai_sdk, tmp_path, monkeypatch, api, resource_export):
    """REGRESSION: AsyncOpenAI import order must not bypass tracing or refusal."""
    if api == "responses" and not _has_responses(openai_sdk):
        pytest.skip("the Responses API needs openai>=1.66")
    body = OPENAI_RESPONSE if api == "responses" else OPENAI_COMPLETION
    kwargs = {"model": "gpt-4o-mini"}
    kwargs.update({"input": "hi"} if api == "responses" else {"messages": [{"role": "user", "content": "hi"}]})
    path = tmp_path / "early-async.jsonl"
    transport = _CountingTransport(openai_sdk, body)
    guard = BudgetGuard(max_calls=1)

    async def run():
        async with openai_sdk.AsyncOpenAI(
            api_key="sk-compat", max_retries=0,
            http_client=openai_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
        ) as early:
            resource = early.responses if api == "responses" else early.chat.completions
            if not resource_export:
                monkeypatch.delattr(openai_sdk, "resources", raising=False)
            patch_openai_async(AsyncTracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
            patch_openai_async(AsyncTracer(), budget_guard=BudgetGuard(max_calls=0))
            await resource.create(**kwargs)
            async with openai_sdk.AsyncOpenAI(
                api_key="sk-compat", max_retries=0,
                http_client=openai_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
            ) as late:
                late_resource = late.responses if api == "responses" else late.chat.completions
                with pytest.raises(BudgetExceeded):
                    await late_resource.create(**kwargs)
            with pytest.raises(BudgetExceeded):
                await resource.create(**kwargs)

    asyncio.run(run())
    _assert_billed_once(guard, path, transport)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("api", ["chat", "responses"])
def test_init_guards_an_existing_openai_client(openai_sdk, tmp_path, asynchronous, api):
    """REGRESSION: public init must guard a previously constructed client."""
    import agentguard

    if api == "responses" and not _has_responses(openai_sdk):
        pytest.skip("the Responses API needs openai>=1.66")
    path = tmp_path / "init-early.jsonl"
    body = OPENAI_RESPONSE if api == "responses" else OPENAI_COMPLETION
    transport = _CountingTransport(openai_sdk, body)
    kwargs = {"model": "gpt-4o-mini"}
    kwargs.update({"input": "hi"} if api == "responses" else {"messages": [{"role": "user", "content": "hi"}]})
    agentguard.shutdown()
    try:
        if asynchronous:
            async def run():
                async with openai_sdk.AsyncOpenAI(
                    api_key="sk-compat", max_retries=0,
                    http_client=openai_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
                ) as client:
                    resource = client.responses if api == "responses" else client.chat.completions
                    agentguard.init(budget_usd=1e-12, trace_file=str(path), local_only=True)
                    with pytest.raises(BudgetExceeded):
                        await resource.create(**kwargs)
                    with pytest.raises(BudgetExceeded):
                        await resource.create(**kwargs)
            asyncio.run(run())
        else:
            with _client(openai_sdk, "OpenAI", transport) as client:
                resource = client.responses if api == "responses" else client.chat.completions
                agentguard.init(budget_usd=1e-12, trace_file=str(path), local_only=True)
                with pytest.raises(BudgetExceeded):
                    resource.create(**kwargs)
                with pytest.raises(BudgetExceeded):
                    resource.create(**kwargs)
        guard = agentguard.get_budget_guard()
    finally:
        agentguard.shutdown()
    _assert_billed_once(guard, path, transport)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("api", ["chat", "responses"])
def test_openai_unpatch_restores_existing_client(openai_sdk, asynchronous, api):
    """The shared resource method must be restored for already-created clients."""
    if api == "responses" and not _has_responses(openai_sdk):
        pytest.skip("the Responses API needs openai>=1.66")
    body = OPENAI_RESPONSE if api == "responses" else OPENAI_COMPLETION
    transport = _CountingTransport(openai_sdk, body)
    guard = BudgetGuard(max_calls=0)
    kwargs = {"model": "gpt-4o-mini"}
    kwargs.update({"input": "hi"} if api == "responses" else {"messages": [{"role": "user", "content": "hi"}]})
    if asynchronous:
        async def run():
            async with openai_sdk.AsyncOpenAI(
                api_key="sk-compat", max_retries=0,
                http_client=openai_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
            ) as client:
                resource = client.responses if api == "responses" else client.chat.completions
                original = resource.create.__func__
                patch_openai_async(AsyncTracer(), budget_guard=guard)
                assert resource.create.__func__ is not original
                unpatch_openai_async()
                assert resource.create.__func__ is original
                await resource.create(**kwargs)
        asyncio.run(run())
    else:
        with _client(openai_sdk, "OpenAI", transport) as client:
            resource = client.responses if api == "responses" else client.chat.completions
            original = resource.create.__func__
            patch_openai(Tracer(), budget_guard=guard)
            assert resource.create.__func__ is not original
            unpatch_openai()
            assert resource.create.__func__ is original
            resource.create(**kwargs)
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 0


def test_openai_chat_stream_bills_once_and_blocks_next_dispatch(openai_sdk, tmp_path):
    path = tmp_path / "chat-stream.jsonl"
    transport = _CountingTransport(openai_sdk, _chat_sse())
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(tmp_path / "budget.json"), key="compat")
    patch_openai(Tracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
    kwargs = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "stream": True}

    with _client(openai_sdk, "OpenAI", transport) as client:
        with client.chat.completions.create(**kwargs) as stream:
            chunks = list(stream)
        assert isinstance(chunks[-1], openai_sdk.types.chat.ChatCompletionChunk)
        assert chunks[-1].usage.total_tokens == 15
        with pytest.raises(BudgetExceeded):
            client.chat.completions.create(**kwargs)

    assert json.loads(transport.requests[0].content)["stream_options"]["include_usage"] is True
    _assert_billed_once(guard, path, transport)
    _assert_stream_settled(guard)


@pytest.mark.parametrize("method", ["create", "stream"])
def test_anthropic_stream_bills_once_and_blocks_next_dispatch(anthropic_sdk, tmp_path, method):
    path = tmp_path / "anthropic-stream.jsonl"
    transport = _CountingTransport(anthropic_sdk, _anthropic_sse())
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(tmp_path / "budget.json"), key="compat")
    patch_anthropic(Tracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
    kwargs = {"model": ANTHROPIC_MESSAGE["model"], "max_tokens": 16,
              "messages": [{"role": "user", "content": "hi"}]}
    if method == "create":
        kwargs["stream"] = True

    with _client(anthropic_sdk, "Anthropic", transport) as client:
        dispatch = getattr(client.messages, method)
        with dispatch(**kwargs) as stream:
            if method == "stream":
                assert list(stream.text_stream) == ["ok"]
                assert stream.get_final_message().usage.output_tokens == 5
            else:
                assert [event.type for event in stream][-1] == "message_stop"
        with pytest.raises(BudgetExceeded), dispatch(**kwargs):
            pass

    _assert_billed_once(guard, path, transport)
    _assert_stream_settled(guard)


@pytest.mark.parametrize("streamed", [False, True])
def test_openai_chat_async_bills_once_and_blocks_next_dispatch(openai_sdk, tmp_path, streamed):
    path = tmp_path / "async-chat.jsonl"
    transport = _CountingTransport(openai_sdk, _chat_sse() if streamed else OPENAI_COMPLETION)
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(tmp_path / "budget.json"), key="compat")
    patch_openai_async(AsyncTracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
    kwargs = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "stream": streamed}

    async def run():
        async with openai_sdk.AsyncOpenAI(
            api_key="sk-compat", max_retries=0,
            http_client=openai_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
        ) as client:
            result = await client.chat.completions.create(**kwargs)
            if streamed:
                async with result as stream:
                    chunks = [chunk async for chunk in stream]
                assert isinstance(chunks[-1], openai_sdk.types.chat.ChatCompletionChunk)
                assert chunks[-1].usage.total_tokens == 15
            else:
                assert isinstance(result, openai_sdk.types.chat.ChatCompletion)
            with pytest.raises(BudgetExceeded):
                await client.chat.completions.create(**kwargs)

    asyncio.run(run())
    _assert_billed_once(guard, path, transport)
    if streamed:
        assert json.loads(transport.requests[0].content)["stream_options"]["include_usage"] is True
        _assert_stream_settled(guard)


@pytest.mark.parametrize("method", ["non_stream", "stream_create", "stream_helper"])
def test_anthropic_async_bills_once_and_blocks_next_dispatch(anthropic_sdk, tmp_path, method):
    streamed = method != "non_stream"
    path = tmp_path / "async-anthropic.jsonl"
    transport = _CountingTransport(anthropic_sdk, _anthropic_sse() if streamed else ANTHROPIC_MESSAGE)
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(tmp_path / "budget.json"), key="compat")
    patch_anthropic_async(AsyncTracer(sink=JsonlFileSink(str(path))), budget_guard=guard)
    kwargs = {"model": ANTHROPIC_MESSAGE["model"], "max_tokens": 16,
              "messages": [{"role": "user", "content": "hi"}]}
    if method == "stream_create":
        kwargs["stream"] = True

    async def run():
        async with anthropic_sdk.AsyncAnthropic(
            api_key="sk-compat", max_retries=0,
            http_client=anthropic_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
        ) as client:
            if method == "stream_helper":
                async with client.messages.stream(**kwargs) as stream:
                    assert [text async for text in stream.text_stream] == ["ok"]
                    assert (await stream.get_final_message()).usage.output_tokens == 5
                with pytest.raises(BudgetExceeded):
                    async with client.messages.stream(**kwargs):
                        pass
            else:
                result = await client.messages.create(**kwargs)
                if streamed:
                    async with result as stream:
                        assert [event.type async for event in stream][-1] == "message_stop"
                else:
                    assert result.usage.input_tokens == 10
                with pytest.raises(BudgetExceeded):
                    await client.messages.create(**kwargs)

    asyncio.run(run())
    _assert_billed_once(guard, path, transport)
    if streamed:
        _assert_stream_settled(guard)


def test_langchain_dispatch_propagates_budget_stop():
    _require("langchain_core")
    from langchain_core.callbacks import CallbackManager

    from agentguard.integrations.langchain import AgentGuardCallbackHandler

    handler = AgentGuardCallbackHandler(budget_guard=BudgetGuard(max_calls=0))
    manager = CallbackManager([handler])
    with pytest.raises(BudgetExceeded):
        manager.on_tool_start({"name": "search"}, "docs")


def test_langgraph_node_budget_stops_the_graph():
    _require("langgraph")
    from typing import TypedDict

    from langgraph.graph import END, StateGraph

    from agentguard.integrations.langgraph import guard_node

    class State(TypedDict):
        n: int

    calls: List[int] = []

    def step(state: State) -> State:
        calls.append(state["n"])
        return {"n": state["n"] + 1}

    guard = BudgetGuard(max_calls=2)
    builder = StateGraph(State)
    builder.add_node("step", guard_node(step, tracer=Tracer(), budget_guard=guard))
    builder.set_entry_point("step")
    builder.add_conditional_edges("step", lambda s: "step" if s["n"] < 10 else END)
    graph = builder.compile()

    with pytest.raises(BudgetExceeded):
        graph.invoke({"n": 0})
    assert calls == [0, 1]


def test_otel_sink_exports_guard_spans():
    _require("opentelemetry.sdk.trace")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from agentguard.sinks.otel import OtelTraceSink

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = Tracer(sink=OtelTraceSink(provider), service="compat")

    with tracer.trace("agent.run") as ctx:
        ctx.event("tool.call", data={"tool": "search"})

    spans = exporter.get_finished_spans()
    assert [span.name for span in spans] == ["agent.run"]
    assert [event.name for event in spans[0].events] == ["tool.call"]


UNMODIFIED_OPENAI_SCRIPT = '''
import importlib
import openai

base = next(c for c in openai.DefaultHttpxClient.__mro__ if c.__name__ == "Client")
http = importlib.import_module(base.__module__.split(".")[0])
body = {
    "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"},
                 "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 200000, "completion_tokens": 100000, "total_tokens": 300000},
}
sent = []

def handle(request):
    sent.append(request)
    return http.Response(200, json=body)

client = openai.OpenAI(api_key="sk-compat", max_retries=0,
                       http_client=openai.DefaultHttpxClient(transport=http.MockTransport(handle)))
try:
    for _ in range(10):
        client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
finally:
    print("dispatched", len(sent))
'''


def test_agentguard_run_stops_an_unmodified_openai_script(tmp_path):
    _require("openai")
    import subprocess
    import sys

    (tmp_path / "agent.py").write_text(UNMODIFIED_OPENAI_SCRIPT, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "agentguard.cli", "run", "--budget-usd", "5",
         "--trace-file", "trace.jsonl", "python", "agent.py"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "AGENTGUARD_API_KEY": "",
             "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert proc.returncode == 1, proc.stderr
    # $1.50 per call: the fourth call returns, records $6.00, and raises. No fifth send.
    assert "dispatched 4" in proc.stdout
    assert "Cost budget exceeded: $6.0000 > $5.0000" in proc.stderr
    events = [json.loads(line) for line in (tmp_path / "trace.jsonl").read_text().splitlines()]
    assert any(e["name"] == "guard.budget_exceeded" for e in events)


# AG-06: the OpenAI Responses API and the Agents SDK.

RESPONSES_USAGE = {
    "input_tokens": 10,
    "input_tokens_details": {"cached_tokens": 4},
    "output_tokens": 5,
    "output_tokens_details": {"reasoning_tokens": 2},
    "total_tokens": 15,
}


def _response(output: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "resp_compat",
        "object": "response",
        "created_at": 0,
        "status": "completed",
        "model": "gpt-4o-mini",
        "output": output,
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "usage": RESPONSES_USAGE,
    }


MESSAGE_OUTPUT = [{
    "type": "message", "id": "msg_1", "status": "completed", "role": "assistant",
    "content": [{"type": "output_text", "text": "ok", "annotations": []}],
}]
TOOL_CALL_OUTPUT = [{
    "type": "function_call", "id": "fc_1", "call_id": "call_1",
    "name": "lookup", "arguments": "{}", "status": "completed",
}]
OPENAI_RESPONSE = _response(MESSAGE_OUTPUT)


def _sse(body: Dict[str, Any]) -> str:
    """response.created without usage, then response.completed with it."""
    created = {**body, "status": "in_progress", "output": [], "usage": None}
    events = [
        {"type": "response.created", "sequence_number": 0, "response": created},
        {"type": "response.completed", "sequence_number": 1, "response": body},
    ]
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)


def _has_responses(sdk):
    # Early Responses releases attach resources in __init__, not on the class.
    # Use the SDK's explicit transport, as the dispatch tests do; older client
    # constructors can otherwise pass removed proxy options to newer httpx.
    with sdk.OpenAI(
        api_key="sk-compat", http_client=sdk.DefaultHttpxClient()
    ) as probe:
        return hasattr(probe, "responses")


@pytest.fixture
def responses_sdk(openai_sdk):
    if not _has_responses(openai_sdk):
        pytest.skip("the Responses API needs openai>=1.66")
    from agentguard.instrument import unpatch_openai_async

    yield openai_sdk
    unpatch_openai_async()


def test_responses_create_counts_once_and_blocks_before_dispatch(responses_sdk):
    transport = _CountingTransport(responses_sdk, OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=1)
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(responses_sdk, "OpenAI", transport)

    response = client.responses.create(model="gpt-4o-mini", input="hi")
    with pytest.raises(BudgetExceeded):
        client.responses.create(model="gpt-4o-mini", input="hi")

    assert isinstance(response, responses_sdk.types.responses.Response)
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15
    # gpt-4o-mini: 6 uncached + 4 cached input, 5 output. The 2 reasoning tokens
    # are inside the 5 output tokens, so they are not billed again.
    assert guard.state.cost_used == pytest.approx(4.2e-6)


def test_responses_parse_counts_once(responses_sdk):
    """parse() is patched on its own; it must not also bill through create()."""
    transport = _CountingTransport(responses_sdk, OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=5)
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(responses_sdk, "OpenAI", transport)

    parsed = client.responses.parse(model="gpt-4o-mini", input="hi")

    assert parsed.usage.total_tokens == 15
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15


def test_responses_stream_counts_final_usage_once(responses_sdk):
    transport = _CountingTransport(responses_sdk, _sse(OPENAI_RESPONSE))
    guard = BudgetGuard(max_calls=2)
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(responses_sdk, "OpenAI", transport)

    with client.responses.create(model="gpt-4o-mini", input="hi", stream=True) as stream:
        kinds = [event.type for event in stream]
    with client.responses.stream(model="gpt-4o-mini", input="hi") as helper:
        final = helper.get_final_response()
    with pytest.raises(BudgetExceeded):
        client.responses.create(model="gpt-4o-mini", input="hi", stream=True)

    assert kinds == ["response.created", "response.completed"]
    assert final.usage.total_tokens == 15
    assert len(transport.requests) == 2
    assert "stream_options" not in json.loads(transport.requests[0].content)
    assert guard.state.calls_used == 2
    assert guard.state.tokens_used == 30


def test_responses_async_create_with_init_tracer(responses_sdk):
    """init() hands the async patch a sync Tracer; calls must still go through."""
    import asyncio

    from agentguard.instrument import patch_openai_async

    transport = _CountingTransport(responses_sdk, OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=1)
    patch_openai_async(Tracer(), budget_guard=guard)
    client = responses_sdk.AsyncOpenAI(
        api_key="sk-compat",
        max_retries=0,
        http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
    )

    async def run() -> Any:
        first = await client.responses.create(model="gpt-4o-mini", input="hi")
        with pytest.raises(BudgetExceeded):
            await client.responses.create(model="gpt-4o-mini", input="hi")
        return first

    assert isinstance(asyncio.run(run()), responses_sdk.types.responses.Response)
    assert len(transport.requests) == 1
    assert guard.state.tokens_used == 15


def test_responses_async_tracer_records_billing_to_a_file(responses_sdk, tmp_path):
    """A real async context emits synchronously, unlike an AsyncMock event."""
    import asyncio

    from agentguard import AsyncTracer, JsonlFileSink
    from agentguard.instrument import patch_openai_async

    path = tmp_path / "async-billing.jsonl"
    transport = _CountingTransport(responses_sdk, OPENAI_RESPONSE)
    guard = BudgetGuard(max_calls=1)
    patch_openai_async(AsyncTracer(sink=JsonlFileSink(str(path))), budget_guard=guard)

    async def run():
        async with responses_sdk.AsyncOpenAI(
            api_key="sk-compat",
            max_retries=0,
            http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
        ) as client:
            await client.responses.create(model="gpt-4o-mini", input="hi")

    asyncio.run(run())
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    billing = [event for event in events if event["name"] == "llm.result"]
    assert len(billing) == 1
    assert billing[0]["cost_usd"] == pytest.approx(4.2e-6)
    assert len(transport.requests) == 1
    assert guard.state.tokens_used == 15


def test_responses_async_streaming_response_counts_on_parse(responses_sdk):
    """with_streaming_response is the path the Agents SDK streams through."""
    import asyncio

    from agentguard.instrument import patch_openai_async

    transport = _CountingTransport(responses_sdk, _sse(OPENAI_RESPONSE))
    guard = BudgetGuard(max_calls=5)
    patch_openai_async(Tracer(), budget_guard=guard)
    client = responses_sdk.AsyncOpenAI(
        api_key="sk-compat",
        max_retries=0,
        http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
    )

    async def run() -> List[str]:
        create = client.responses.with_streaming_response.create
        async with create(model="gpt-4o-mini", input="hi", stream=True) as raw:
            assert raw.request_id is None or isinstance(raw.request_id, str)
            return [event.type async for event in await raw.parse()]

    assert asyncio.run(run()) == ["response.created", "response.completed"]
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 15


def test_responses_async_streaming_response_counts_when_left_unread(responses_sdk):
    """Leaving the with_streaming_response block without reading still counts the call."""
    import asyncio

    from agentguard.instrument import patch_openai_async

    transport = _CountingTransport(responses_sdk, _sse(OPENAI_RESPONSE))
    guard = BudgetGuard(max_calls=5)
    patch_openai_async(Tracer(), budget_guard=guard)
    client = responses_sdk.AsyncOpenAI(
        api_key="sk-compat",
        max_retries=0,
        http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
    )

    async def run() -> None:
        create = client.responses.with_streaming_response.create
        async with create(model="gpt-4o-mini", input="hi", stream=True):
            pass

    asyncio.run(run())
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 1


def test_responses_raw_response_reserves_with_a_store(responses_sdk, tmp_path):
    """Two workers race one stored call through with_raw_response; one is sent."""
    import threading
    import time

    class _Slow(_CountingTransport):
        def _handle(self, request: Any) -> Any:
            time.sleep(0.3)  # both workers are past preflight before either records usage
            return super()._handle(request)

    transport = _Slow(responses_sdk, OPENAI_RESPONSE)
    store = JsonFileStateStore(tmp_path / "budget.json")
    patch_openai(Tracer(), budget_guard=BudgetGuard(max_calls=1, store=store, key="raw"))
    clients = [_client(responses_sdk, "OpenAI", transport) for _ in range(2)]
    barrier = threading.Barrier(2)
    outcomes: List[str] = []

    def worker(client: Any) -> None:
        barrier.wait(5)
        try:
            raw = client.responses.with_raw_response.create(model="gpt-4o-mini", input="hi")
            outcomes.append(str(raw.parse().usage.total_tokens))
        except BudgetExceeded:
            outcomes.append("blocked")

    threads = [threading.Thread(target=worker, args=(c,)) for c in clients]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)

    assert sorted(outcomes) == ["15", "blocked"]
    assert len(transport.requests) == 1
    settled = BudgetGuard(max_calls=1, store=store, key="raw").reservation_totals()["settled"]
    assert settled["calls"] == 1 and settled["tokens"] == 15


def test_responses_provider_error_propagates_and_is_not_billed(responses_sdk):
    class _Failing(_CountingTransport):
        def _handle(self, request: Any) -> Any:
            self.requests.append(request)
            return self._http.Response(400, json={"error": {"message": "bad", "type": "x"}})

    transport = _Failing(responses_sdk, {})
    guard = BudgetGuard(max_calls=5)
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(responses_sdk, "OpenAI", transport)

    with pytest.raises(responses_sdk.BadRequestError):
        client.responses.create(model="gpt-4o-mini", input="hi")
    assert len(transport.requests) == 1
    assert guard.state.calls_used == 0


def test_responses_store_backed_dollar_cap_reserves_max_output_tokens(responses_sdk, tmp_path):
    from agentguard._reservation_contract import MissingBound

    transport = _CountingTransport(responses_sdk, OPENAI_RESPONSE)
    store = JsonFileStateStore(tmp_path / "budget.json")
    guard = BudgetGuard(max_cost_usd=5.0, store=store, key="responses")
    patch_openai(Tracer(), budget_guard=guard)
    client = _client(responses_sdk, "OpenAI", transport)

    with pytest.raises(MissingBound):
        client.responses.create(model="gpt-4o-mini", input="hi")
    client.responses.create(model="gpt-4o-mini", input="hi", max_output_tokens=64)

    assert len(transport.requests) == 1
    assert guard.reservation_totals()["settled"]["calls"] == 1


def _agent_transport(sdk: Any, turns: List[List[Dict[str, Any]]]) -> _CountingTransport:
    """Answer each model call with the next scripted output, streamed when asked."""
    transport = _CountingTransport(sdk, {})

    def handle(request: Any) -> Any:
        transport.requests.append(request)
        body = _response(turns[min(len(transport.requests), len(turns)) - 1])
        if json.loads(request.content).get("stream"):
            return transport._http.Response(
                200, text=_sse(body), headers={"content-type": "text/event-stream"}
            )
        return transport._http.Response(200, json=body)

    transport.transport = transport._http.MockTransport(handle)
    return transport


@pytest.mark.parametrize("streamed", [False, True])
def test_agents_sdk_run_stops_a_tool_loop_before_the_next_model_call(responses_sdk, streamed):
    """The patch sits under the Agents SDK model call and composes with max_turns."""
    import asyncio

    agents = _require("agents")
    from agentguard.instrument import patch_openai_async

    agents.set_tracing_disabled(True)
    guard = BudgetGuard(max_calls=3)
    patch_openai_async(Tracer(), budget_guard=guard)
    # The model asks for the same tool every turn: a loop.
    transport = _agent_transport(responses_sdk, [TOOL_CALL_OUTPUT])
    client = responses_sdk.AsyncOpenAI(
        api_key="sk-compat",
        max_retries=0,
        http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
    )

    @agents.function_tool
    def lookup() -> str:
        return "nothing yet"

    agent = agents.Agent(
        name="looper",
        tools=[lookup],
        model=agents.OpenAIResponsesModel("gpt-4o-mini", client),
    )
    run_config = agents.RunConfig(model_provider=agents.OpenAIProvider(openai_client=client))

    async def run() -> None:
        if streamed:
            result = agents.Runner.run_streamed(agent, "hi", max_turns=10, run_config=run_config)
            async for _ in result.stream_events():
                pass
        else:
            await agents.Runner.run(agent, "hi", max_turns=10, run_config=run_config)

    with pytest.raises(BudgetExceeded):
        asyncio.run(run())
    assert len(transport.requests) == 3
    assert guard.state.calls_used == 3
    assert guard.state.tokens_used == 45


def test_agents_sdk_native_max_turns_still_applies(responses_sdk):
    import asyncio

    agents = _require("agents")
    from agentguard.instrument import patch_openai_async

    agents.set_tracing_disabled(True)
    guard = BudgetGuard(max_calls=10)
    patch_openai_async(Tracer(), budget_guard=guard)
    transport = _agent_transport(responses_sdk, [TOOL_CALL_OUTPUT])
    client = responses_sdk.AsyncOpenAI(
        api_key="sk-compat",
        max_retries=0,
        http_client=responses_sdk.DefaultAsyncHttpxClient(transport=transport.transport),
    )

    @agents.function_tool
    def lookup() -> str:
        return "nothing yet"

    agent = agents.Agent(
        name="looper", tools=[lookup], model=agents.OpenAIResponsesModel("gpt-4o-mini", client)
    )
    run_config = agents.RunConfig(model_provider=agents.OpenAIProvider(openai_client=client))
    with pytest.raises(agents.MaxTurnsExceeded):
        asyncio.run(agents.Runner.run(agent, "hi", max_turns=2, run_config=run_config))
    assert len(transport.requests) == 2
    assert guard.state.calls_used == 2
