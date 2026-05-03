from __future__ import annotations

import importlib.util
import io
import json
import urllib.request
from pathlib import Path

from conftest import EXPECTED_API_KEY, IngestHandler

EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "examples" / "sticky_agent_proof.py"


def _load_example_module():
    spec = importlib.util.spec_from_file_location("sticky_agent_proof", EXAMPLE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sticky_agent_proof_writes_local_and_hosted_artifacts(tmp_path):
    module = _load_example_module()
    output = io.StringIO()

    paths = module.run_sticky_agent_proof(tmp_path, stream=output)

    assert paths["trace"].exists()
    assert paths["hosted"].exists()
    assert paths["incident"].exists()
    text = output.getvalue()
    assert "No API keys. No network." in text
    assert "stopped retry storm" in text
    assert "stopped repeated tool loop" in text
    assert "stopped budget burn" in text

    local_events = [
        json.loads(line)
        for line in paths["trace"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    hosted_events = [
        json.loads(line)
        for line in paths["hosted"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    names = [event["name"] for event in local_events]

    assert "guard.retry_limit_exceeded" in names
    assert "guard.loop_detected" in names
    assert "guard.budget_warning" in names
    assert "guard.budget_exceeded" in names
    assert hosted_events
    assert len(hosted_events) == len(local_events)
    assert all(event["kind"] in {"span", "event"} for event in hosted_events)
    assert all(event["type"] == event["kind"] for event in hosted_events)
    assert all(event["service"] == module.SERVICE for event in hosted_events)

    incident = paths["incident"].read_text(encoding="utf-8")
    assert "# AgentGuard Incident Report" in incident
    assert "retry_limit_exceeded" in incident
    assert "retained history, alerts, spend trends" in incident


def test_sticky_agent_proof_hosted_ndjson_matches_ingest_contract(tmp_path, ingest_url):
    module = _load_example_module()
    paths = module.run_sticky_agent_proof(tmp_path, stream=io.StringIO())

    request = urllib.request.Request(
        ingest_url,
        data=paths["hosted"].read_bytes(),
        headers={
            "Authorization": f"Bearer {EXPECTED_API_KEY}",
            "Content-Type": "application/x-ndjson",
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode())

    request_log = IngestHandler.request_log()
    assert payload["accepted"] > 0
    assert payload["rejected"] == 0
    assert request_log[-1]["status"] == 200
