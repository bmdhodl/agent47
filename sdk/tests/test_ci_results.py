"""A required CI summary cannot turn skipped or missing coverage green."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
JOBS = ("test", "lint", "mcp", "mcp-budget", "compat")


def run_gate(payload):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_ci_results.py")],
        env={**os.environ, "CI_NEEDS": payload}, capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=15,
    )


def test_every_required_job_must_pass():
    result = run_gate(json.dumps({name: {"result": "success"} for name in JOBS}))
    assert result.returncode == 0
    assert "All five CI job groups passed" in result.stdout


@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", None, "unknown"])
def test_non_success_result_blocks_merge(result):
    payload = {name: {"result": "success"} for name in JOBS}
    payload["compat"]["result"] = result
    checked = run_gate(json.dumps(payload))
    assert checked.returncode == 1
    assert "compat" in checked.stderr


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
