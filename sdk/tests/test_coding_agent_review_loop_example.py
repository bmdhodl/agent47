from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from agentguard.evaluation import summarize_trace


def _load_example():
    root = Path(__file__).resolve().parents[2]
    path = root / "examples" / "coding_agent_review_loop.py"
    spec = importlib.util.spec_from_file_location("coding_agent_review_loop", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_loop_example_does_not_double_count_cumulative_guard_cost(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = _load_example()

    assert module.main() == 0

    trace_path = tmp_path / module.TRACE_FILE
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    budget_events = [event for event in events if event["name"] == "guard.budget_exceeded"]

    assert len(budget_events) == 1
    assert "cost_usd" not in budget_events[0]["data"]
    assert budget_events[0]["data"]["total_cost_usd"] == pytest.approx(0.051)
    assert summarize_trace(str(trace_path))["cost_usd"] == pytest.approx(0.051)
