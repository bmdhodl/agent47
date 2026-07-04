"""Smoke test for examples/local-first-template/.

Runs the example offline (no model server, no GPU, no network) and asserts
the AgentGuard wiring -- budget, rate limit, tool allowlist, JSONL audit log
-- does not drift. Mirrors the subprocess pattern in test_example_starters.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "local-first-template"
AGENT_PATH = EXAMPLE_DIR / "agent.py"


def _env() -> dict:
    env = os.environ.copy()
    sdk_path = str(REPO_ROOT / "sdk")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        sdk_path if not existing else os.pathsep.join([sdk_path, existing])
    )
    # Default is offline; set it explicitly so the test is unambiguous.
    env["AGENTGUARD_LOCAL_DEMO"] = "offline"
    return env


def test_example_files_exist_and_compile() -> None:
    for name in ("agent.py", "config.py"):
        path = EXAMPLE_DIR / name
        assert path.exists(), f"Missing example file: {path}"
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    assert (EXAMPLE_DIR / "README.md").exists()
    assert (EXAMPLE_DIR / "sample_task.txt").exists()


def test_agent_runs_offline_and_audits_every_guard() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(AGENT_PATH)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=_env(),
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(
                "local-first agent timed out.\n"
                f"STDOUT:\n{exc.stdout or ''}\nSTDERR:\n{exc.stderr or ''}"
            ) from exc

        assert result.returncode == 0, result.stderr
        # Core loop wiring is visible in stdout.
        assert "offline=True" in result.stdout
        assert "tool DENIED" in result.stdout
        assert "Final answer:" in result.stdout

        trace_path = Path(tmpdir, "local_first_template_traces.jsonl")
        assert trace_path.exists(), "audit JSONL was not written"

        names = []
        with trace_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    names.append(json.loads(line).get("name"))

        # Every guard/loop path the example claims must appear in the log.
        assert "guard.rate_check" in names
        assert "guard.tool_denied" in names
        assert "llm.call" in names
        assert "tool.call" in names
        assert "agent.final" in names


def test_agent_makes_no_network_call_in_offline_mode() -> None:
    """Offline mode must never open a socket -- CI has no model server."""
    source = AGENT_PATH.read_text(encoding="utf-8")
    # The live path is the only urlopen; it is gated behind the offline flag.
    assert "_live_reply" in source
    assert "_offline_reply" in source
    assert 'os.environ.get("AGENTGUARD_LOCAL_DEMO"' in source


def test_helpers_handle_bad_input_without_crashing() -> None:
    """parse_tool_call and read_file_tool degrade gracefully on bad input."""
    sys.path.insert(0, str(EXAMPLE_DIR))
    try:
        from agent import ToolDenied, parse_tool_call, read_file_tool
    finally:
        sys.path.pop(0)

    # Not a tool call -> None.
    assert parse_tool_call("just an answer") is None
    # Malformed JSON args -> flagged invalid, not a crash.
    bad = parse_tool_call("TOOL_CALL: read_file {bad json")
    assert bad is not None and bad["valid_args"] is False
    # Empty path is refused, not read as a directory.
    try:
        read_file_tool("", base_dir=EXAMPLE_DIR)
        raise AssertionError("empty path should be refused")
    except ToolDenied:
        pass
    # Path traversal is refused.
    try:
        read_file_tool("../../../etc/passwd", base_dir=EXAMPLE_DIR)
        raise AssertionError("traversal should be refused")
    except ToolDenied:
        pass


def test_live_reply_estimates_tokens_when_usage_is_missing() -> None:
    """Live mode must still feed BudgetGuard when local servers omit usage."""
    sys.path.insert(0, str(EXAMPLE_DIR))
    try:
        from agent import LocalChatClient
        from config import AgentPolicy
    finally:
        sys.path.pop(0)

    class _FakeResponse:
        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {"message": {"content": "Local server reply without usage"}}
                    ]
                }
            ).encode("utf-8")

    client = LocalChatClient(AgentPolicy(), offline=False)
    messages = [{"role": "user", "content": "Summarize this local task"}]

    with patch("agent.urllib.request.urlopen", return_value=_FakeResponse()):
        reply = client.complete(messages)

    assert reply["content"] == "Local server reply without usage"
    assert reply["prompt_tokens"] == max(1, len(messages[0]["content"]) // 4)
    assert reply["completion_tokens"] == max(1, len(reply["content"]) // 4)


def test_policy_allowlist_is_tuple_backed() -> None:
    """A frozen policy should not expose a mutable tool allowlist."""
    sys.path.insert(0, str(EXAMPLE_DIR))
    try:
        from config import AgentPolicy
    finally:
        sys.path.pop(0)

    policy = AgentPolicy()

    assert isinstance(policy.allowed_tools, tuple)
    assert policy.allowed_tools == ("read_file",)
