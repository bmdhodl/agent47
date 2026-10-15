"""A required CI summary cannot turn skipped or missing coverage green."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
JOBS = ("test", "lint", "mcp", "mcp-budget", "compat", "responses-floor")


@pytest.mark.parametrize("filename", [
    "ci.yml", "actionlint.yml", "docs-consistency.yml", "codeql.yml", "trustabl.yml", "claude-review.yml",
])
def test_REGRESSION_local_ci_never_checks_out_fork_code(filename):
    # Local PR jobs must exclude fork heads. The always-running summary rejects
    # a fork before checkout so skipped test groups cannot turn the gate green.
    workflow = yaml.safe_load((ROOT / ".github/workflows" / filename).read_text(encoding="utf-8"))
    for name, job in workflow["jobs"].items():
        assert job["runs-on"] == ["self-hosted", "linux", "x64", "pc"]
        if name == "ci-required":
            assert "always()" in job["if"]
            first = job["steps"][0]
            assert "github.event_name == 'pull_request'" in first["if"]
            assert "github.event.pull_request.head.repo.full_name != github.repository" in first["if"]
            assert first["run"].rstrip().endswith("exit 1")
            assert "uses" not in first
        elif name == "claude-review":
            assert "github.event.pull_request.head.repo.full_name == github.repository" in job["if"]
            checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
            assert checkout["with"]["ref"] == "${{ github.sha }}"
            assert checkout["with"]["persist-credentials"] is False
        else:
            assert "github.event_name != 'pull_request'" in job["if"]
            assert "github.event.pull_request.head.repo.full_name == github.repository" in job["if"]


def run_gate(payload):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_ci_results.py")],
        env={**os.environ, "CI_NEEDS": payload}, capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=15,
    )


def test_every_required_job_must_pass():
    result = run_gate(json.dumps({name: {"result": "success"} for name in JOBS}))
    assert result.returncode == 0
    assert "All 6 CI job groups passed" in result.stdout


@pytest.mark.parametrize("job", JOBS)
@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", None, "unknown"])
def test_non_success_result_blocks_merge(job, result):
    payload = {name: {"result": "success"} for name in JOBS}
    payload[job]["result"] = result
    checked = run_gate(json.dumps(payload))
    assert checked.returncode == 1
    assert job in checked.stderr


@pytest.mark.parametrize("payload", ["", "{}", "null", "[]", '{"test": "success"}', "invalid"])
def test_missing_or_malformed_evidence_blocks_merge(payload):
    assert run_gate(payload).returncode == 1


@pytest.mark.parametrize("row", [None, "success", [], {}])
def test_malformed_job_evidence_blocks_merge(row):
    payload = {name: {"result": "success"} for name in JOBS}
    payload["lint"] = row
    assert run_gate(json.dumps(payload)).returncode == 1


@pytest.mark.parametrize("change", ["missing", "unexpected"])
def test_job_inventory_must_match_required_groups(change):
    payload = {name: {"result": "success"} for name in JOBS}
    if change == "missing":
        del payload["compat"]
    else:
        payload["surprise"] = {"result": "success"}
    assert run_gate(json.dumps(payload)).returncode == 1


@pytest.mark.parametrize("missing_job", JOBS)
def test_missing_required_group_blocks_merge(missing_job):
    payload = {name: {"result": "success"} for name in JOBS}
    del payload[missing_job]
    assert run_gate(json.dumps(payload)).returncode == 1
