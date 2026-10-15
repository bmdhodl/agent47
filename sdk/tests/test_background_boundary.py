"""Characterize detached work outside the same-interpreter runner boundary."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_uninstrumented_child_can_continue_after_guarded_parent_exits(tmp_path):
    script = ROOT / "examples/enforcement_boundary/background_child.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "sdk")
    result = subprocess.run(
        [sys.executable, str(script), "--scratch-parent", str(tmp_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["guarded_parent_exit_code"] == 0
    assert payload["mock_calls_after_parent_exit"] == 2
    assert payload["child_completed"] is True
    assert payload["network_calls"] == 0
    assert payload["coverage"] == "unsupported"
