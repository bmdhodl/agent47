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


def test_reproduction_ignores_inherited_trace_destination(tmp_path):
    script = ROOT / "examples/enforcement_boundary/background_child.py"
    outside = tmp_path / "unowned-output" / "trace.jsonl"
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("AGENTGUARD_")}
    env["PYTHONPATH"] = str(ROOT / "sdk")
    env["AGENTGUARD_TRACE_FILE"] = str(outside)
    result = subprocess.run(
        [sys.executable, str(script), "--scratch-parent", str(tmp_path)],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=45, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert result.returncode == 0, result.stderr
    assert not outside.parent.exists(), "The offline example wrote outside its owned scratch"


def test_reproduction_ignores_inherited_remote_sink_credentials(tmp_path):
    # Fail before any socket can connect, even if a future regression enables
    # a remote sink. sitecustomize also runs in the guarded parent interpreter.
    network_attempt = tmp_path / "network-attempt"
    (tmp_path / "sitecustomize.py").write_text(
        "import socket\nfrom pathlib import Path\n"
        "def reject(*args, **kwargs):\n"
        f"    Path({str(network_attempt)!r}).touch()\n"
        "    raise RuntimeError('offline example attempted network access')\n"
        "socket.getaddrinfo = reject\nsocket.socket.connect = reject\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(tmp_path), str(ROOT / "sdk")])
    env["AGENTGUARD_API_KEY"] = "synthetic-never-send-this-key"
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples/enforcement_boundary/background_child.py"),
         "--scratch-parent", str(tmp_path)],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=45, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert result.returncode == 0, result.stderr
    assert not network_attempt.exists(), "The offline example initialized network access"
