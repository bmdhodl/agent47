"""Exercise the local-accounting example that users copy from the guide."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agentguard import BudgetExceeded, resolve_billable_cost
from agentguard.cli import _report
from agentguard.reporting import render_incident_report

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_local_cost_guide_example_records_free_usage_and_refuses_next_call(tmp_path, monkeypatch, capsys):
    """REGRESSION: the guide must demonstrate real local accounting, not patch promises."""
    guide = (REPO_ROOT / "docs/competitive/vercel-ai-gateway.md").read_text(encoding="utf-8")
    snippets = re.findall(r"```python\n(.*?)\n```", guide, flags=re.DOTALL)
    assert len(snippets) == 1
    monkeypatch.chdir(tmp_path)
    namespace = {}
    exec(compile(snippets[0], "local-cost-guide", "exec"), namespace)

    budget = namespace["budget"]
    assert budget.state.tokens_used == 2500
    assert budget.state.calls_used == 1
    assert budget.state.cost_used == 0
    assert namespace["resolved"]["source"] == "zero"
    with pytest.raises(BudgetExceeded):
        budget.check()

    trace = tmp_path / ".agentguard/traces.jsonl"
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    results = [event for event in events if event["name"] == "llm.result"]
    assert len(results) == 1
    assert results[0]["data"]["total_tokens"] == 2500
    assert results[0]["cost_usd"] == 0
    _report(str(trace), as_json=True)
    report = json.loads(capsys.readouterr().out)
    assert report["llm_results"] == 1
    assert report["estimated_cost_usd"] == 0
    assert json.loads(render_incident_report(str(trace), output_format="json"))["cost_usd"] == 0


def test_same_usage_with_paid_or_unknown_provider_retains_conservative_cost():
    """The free manual example must not imply that unknown OpenAI pricing is free."""
    response = {"usage": {"prompt_tokens": 2000, "completion_tokens": 500, "total_tokens": 2500}}
    resolved = resolve_billable_cost(response, model="unpriced-local-example", provider="openai")
    assert resolved["tokens"]["total"] == 2500
    assert resolved["source"] == "overestimate"
    assert resolved["cost_usd"] > 0
