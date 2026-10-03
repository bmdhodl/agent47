"""Native Ollama accounting through the existing public billing helpers."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agentguard import BudgetExceeded, BudgetGuard, JsonlFileSink, Tracer, consume_billable
from agentguard.cli import _report
from agentguard.precision_cost import extract_tokens, resolve_billable_cost
from agentguard.usage import normalize_usage


def _native_response(endpoint, as_object=False):
    payload = {
        "model": "qwen3.5:4b", "done": True,
        "prompt_eval_count": 2000, "eval_count": 500,
    }
    if endpoint == "chat":
        payload["message"] = {"role": "assistant", "content": "ok"}
    else:
        payload["response"] = "ok"
    return SimpleNamespace(**payload) if as_object else payload


@pytest.mark.parametrize("endpoint", ["chat", "generate"])
@pytest.mark.parametrize("as_object", [False, True], ids=["dict", "attributes"])
def test_ollama_native_fields_count(endpoint, as_object):
    """REGRESSION: native API responses must contribute their actual tokens."""
    response = _native_response(endpoint, as_object)
    resolved = resolve_billable_cost(
        response, model="qwen3.5:4b", provider="ollama", free_local=True,
    )
    assert resolved["tokens"]["input"] == 2000
    assert resolved["tokens"]["output"] == 500
    assert resolved["tokens"]["total"] == 2500
    assert resolved["source"] == "zero"
    assert resolved["cost_usd"] == 0


@pytest.mark.parametrize("endpoint", ["chat", "generate"])
@pytest.mark.parametrize("as_object", [False, True], ids=["dict", "attributes"])
def test_ollama_native_consumption_trips_token_budget(endpoint, as_object, caplog):
    """REGRESSION: manual consumption records the crossing call before raising."""
    caplog.set_level("INFO", logger="agentguard.precision_cost")
    guard = BudgetGuard(max_tokens=1000)
    with pytest.raises(BudgetExceeded):
        consume_billable(
            guard, _native_response(endpoint, as_object), model="qwen3.5:4b",
            provider="ollama", free_local=True,
        )
    assert guard.state.tokens_used == 2500
    assert guard.state.calls_used == 1
    assert guard.state.cost_used == 0
    with pytest.raises(BudgetExceeded):
        guard.check()
    messages = [record.getMessage() for record in caplog.records
                if record.name == "agentguard.precision_cost"]
    assert len(messages) == 1
    assert "input=2000 output=500" in messages[0]
    assert "cost_usd=0.0 source_of_cost=zero" in messages[0]


def test_ollama_native_consume_log_reports_usage():
    guard = BudgetGuard(max_tokens=4000)
    resolved = consume_billable(
        guard, _native_response("chat"), model="qwen3.5:4b",
        provider="ollama", free_local=True,
    )
    assert resolved["consume_log"]["total_tokens"] == 2500
    assert guard.state.tokens_used == 2500
    assert guard.state.calls_used == 1
    assert guard.state.cost_used == 0


def test_ollama_native_manual_trace_and_report(tmp_path, capsys):
    """REGRESSION: callers can retain normalized usage in a local JSONL trace."""
    guard = BudgetGuard(max_tokens=4000)
    resolved = consume_billable(
        guard, _native_response("generate"), model="qwen3.5:4b",
        provider="ollama", free_local=True,
    )
    path = tmp_path / "native.jsonl"
    tracer = Tracer(sink=JsonlFileSink(str(path)), service="native-ollama-test")
    with tracer.trace("agent.run") as span:
        # consume_billable returns a record; this explicit event writes JSONL.
        span.event("llm.result", data=resolved["consume_log"], cost_usd=resolved["cost_usd"])
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    result = next(event for event in events if event["name"] == "llm.result")
    assert result["data"]["input_tokens"] == 2000
    assert result["data"]["output_tokens"] == 500
    assert result["data"]["total_tokens"] == 2500
    assert result["cost_usd"] == 0
    _report(str(path), as_json=True)
    report = json.loads(capsys.readouterr().out)
    assert report["llm_results"] == 1
    assert report["estimated_cost_usd"] == 0


@pytest.mark.parametrize("payload, expected", [
    ({"prompt_eval_count": 0, "eval_count": 0}, (0, 0)),
    ({"prompt_eval_count": 9}, (9, 0)),
    ({"eval_count": 4}, (0, 4)),
    ({"prompt_eval_count": 3, "eval_count": 0}, (3, 0)),
])
def test_ollama_native_zero_partial_counts(payload, expected):
    tokens = extract_tokens(payload, provider="ollama")
    assert (tokens["input"], tokens["output"]) == expected
    assert tokens["total"] == sum(expected)


def test_ollama_native_does_not_imply_free_cost():
    resolved = resolve_billable_cost(
        _native_response("chat"), model="unpriced-model", provider="paid-test",
    )
    assert resolved["tokens"]["total"] == 2500
    assert resolved["source"] == "overestimate"
    assert resolved["cost_usd"] > 0


def test_ollama_native_preserves_explicit_nested_usage():
    payload = _native_response("chat")
    payload["usage"] = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    assert extract_tokens(payload, provider="openai")["total"] == 15


def test_ollama_native_cache_is_not_added_to_total():
    payload = _native_response("generate")
    payload["prompt_eval_cached_count"] = 500
    normalized = normalize_usage(payload, provider="ollama")
    assert normalized["cached_input_tokens"] == 500
    assert normalized["total_tokens"] == 2500
    assert extract_tokens(payload, provider="ollama")["cached"] == 500


def test_ollama_native_stream_partial_is_unmeasured():
    payload = {"model": "qwen3.5:4b", "done": False, "response": "o"}
    assert extract_tokens(payload, provider="ollama")["total"] == 0
