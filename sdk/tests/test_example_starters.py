from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agentguard.quickstart import FRAMEWORK_CHOICES, _build_quickstart_payload

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTERS_ROOT = REPO_ROOT / "examples" / "starters"


def test_quickstart_payloads_have_matching_starter_files() -> None:
    for framework in FRAMEWORK_CHOICES:
        payload = _build_quickstart_payload(
            framework=framework,
            service="my-agent",
            budget_usd=5.0,
            trace_file=".agentguard/traces.jsonl",
        )
        starter_path = STARTERS_ROOT / payload["filename"]
        assert starter_path.exists(), f"Missing starter file for {framework}: {starter_path}"
        compile(
            starter_path.read_text(encoding="utf-8"),
            str(starter_path),
            "exec",
            flags=0,
            dont_inherit=True,
        )


def test_raw_starter_runs_and_writes_trace() -> None:
    starter_path = STARTERS_ROOT / "agentguard_raw_quickstart.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(starter_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Starter timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "Completed local raw starter run." in result.stdout
        assert Path(tmpdir, ".agentguard", "traces.jsonl").exists()
