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
