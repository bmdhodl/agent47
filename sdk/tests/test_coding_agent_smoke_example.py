from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from conftest import IngestHandler

from agentguard.evaluation import _load_events

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = REPO_ROOT / "examples" / "coding_agent_smoke.py"


def _load_example_module():
    spec = importlib.util.spec_from_file_location("coding_agent_smoke", EXAMPLE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_smoke_example_runs_locally_and_trips_guards(tmp_path: Path) -> None:
    module = _load_example_module()
    trace_path = tmp_path / "smoke.jsonl"

    summary = module.run_smoke_agent(
        trace_file=str(trace_path),
        service="test-coding-agent-smoke",
        dashboard=False,
    )

    assert summary["status"] == "ok"
    assert summary["dashboard_enabled"] is False
    assert summary["loop_guard_triggered"] is True
    assert summary["retry_guard_triggered"] is True
    assert "agentguard doctor" in summary["healthy_answer"]
    assert trace_path.exists()

    events = _load_events(str(trace_path))
    names = [event.get("name") for event in events]
    assert "agent.answer" in names
    assert "guard.loop_detected" in names
    assert "guard.retry_limit_exceeded" in names


def test_smoke_example_dashboard_mode_mirrors_to_ingest(tmp_path: Path, ingest_server, monkeypatch) -> None:
    module = _load_example_module()
    host, port = ingest_server
    trace_path = tmp_path / "smoke-dashboard.jsonl"

    monkeypatch.setenv("AGENTGUARD_API_KEY", "ag_test_key_e2e")
    monkeypatch.setenv("AGENTGUARD_DASHBOARD_URL", f"http://{host}:{port}")
    IngestHandler.reset()

    summary = module.run_smoke_agent(
        trace_file=str(trace_path),
        service="test-coding-agent-dashboard",
        dashboard=True,
        _allow_private_dashboard_url=True,
    )

    assert summary["dashboard_enabled"] is True
    assert IngestHandler.event_count() > 0

    traces = {}
    for event in IngestHandler.events:
        traces.setdefault(event.get("trace_id"), []).append(event)
    assert summary["healthy_trace_id"] in traces
    assert summary["loop_trace_id"] in traces
    assert summary["retry_trace_id"] in traces


def test_smoke_example_cli_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_example_module()
    trace_path = tmp_path / "smoke-cli.jsonl"
    monkeypatch.chdir(tmp_path)

    exit_code = module.main(["--trace-file", str(trace_path), "--json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "ok"
    assert payload["trace_file"] == str(trace_path)
    assert payload["loop_guard_triggered"] is True
    assert payload["retry_guard_triggered"] is True
