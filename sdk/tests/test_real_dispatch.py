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

import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agentguard import BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer
from agentguard.instrument import (
    patch_anthropic,
    patch_openai,
    unpatch_anthropic,
    unpatch_openai,
)


def _require(module: str) -> Any:
    if os.environ.get("AGENTGUARD_REQUIRE_REAL_DEPS") == "1":
        return importlib.import_module(module)
    return pytest.importorskip(module)


class _CountingTransport:
    """Mock transport, built from the httpx flavor the SDK itself uses."""

    def __init__(self, sdk: Any, body: Dict[str, Any]) -> None:
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


@pytest.fixture
def anthropic_sdk():
    yield _require("anthropic")
    unpatch_anthropic()


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


@pytest.fixture
def responses_sdk(openai_sdk):
    if not hasattr(openai_sdk.OpenAI, "responses"):
        pytest.skip("the Responses API needs openai>=1.66")
    from agentguard.instrument import unpatch_openai_async

    yield openai_sdk
    unpatch_openai_async()


def _chat_equivalent_cost() -> float:
    from agentguard.precision_cost import resolve_billable_cost

    usage = {
        "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
        "prompt_tokens_details": {"cached_tokens": 4},
        "completion_tokens_details": {"reasoning_tokens": 2},
    }
    return resolve_billable_cost({"usage": usage}, model="gpt-4o-mini", provider="openai")["cost_usd"]


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
    # Same bill as the Chat Completions shape: cached and reasoning tokens priced alike.
    assert guard.state.cost_used == pytest.approx(_chat_equivalent_cost())
    assert guard.state.cost_used > 0


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

    async def run() -> None:
        if streamed:
            result = agents.Runner.run_streamed(agent, "hi", max_turns=10)
            async for _ in result.stream_events():
                pass
        else:
            await agents.Runner.run(agent, "hi", max_turns=10)

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
    with pytest.raises(agents.MaxTurnsExceeded):
        asyncio.run(agents.Runner.run(agent, "hi", max_turns=2))
    assert len(transport.requests) == 2
    assert guard.state.calls_used == 2
