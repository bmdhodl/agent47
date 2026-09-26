import io
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agentguard.hooks import (
    Refusal,
    check_and_record,
    install_settings,
    record_result,
    run,
    signature,
    uninstall_settings,
)
from agentguard.receipt import build_receipt

CAPS = {"loop_max": 3, "retry_max": 2, "max_calls": None}
SDK = str(Path(__file__).resolve().parents[1])


def _event(project, name="PreToolUse", command="npm test", session="s1"):
    return {
        "session_id": session,
        "hook_event_name": name,
        "cwd": str(project),
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": "run it"},
    }


def _run(project, **kwargs):
    stderr = io.StringIO()
    code = run(io.StringIO(json.dumps(_event(project, **kwargs))), stderr)
    return code, stderr.getvalue()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    return tmp_path


def test_third_identical_call_in_a_row_is_refused():
    state = check_and_record(None, "a", "Bash(npm test)", CAPS)
    state = check_and_record(state, "a", "Bash(npm test)", CAPS)
    with pytest.raises(Refusal, match="ran 2 times in a row") as refusal:
        check_and_record(state, "a", "Bash(npm test)", CAPS)
    assert refusal.value.kind == "loop"


def test_edit_test_edit_test_is_not_a_loop():
    state = None
    for sig in ["edit1", "test", "edit2", "test", "edit3", "test"]:
        state = check_and_record(state, sig, sig, CAPS)
    assert state["calls"] == 6


def test_failed_call_is_refused_after_retry_max_even_with_calls_between():
    state = None
    for _ in range(2):
        state = check_and_record(state, "install", "Bash(pip install x)", CAPS)
        state = record_result(state, "install", failed=True)
        state = check_and_record(state, "look", "Read(log)", CAPS)
    with pytest.raises(Refusal, match="already failed 2 times") as refusal:
        check_and_record(state, "install", "Bash(pip install x)", CAPS)
    assert refusal.value.kind == "retry"


def test_success_clears_failures():
    state = check_and_record(None, "x", "x", CAPS)
    state = record_result(state, "x", failed=True)
    state = record_result(state, "x", failed=False)
    assert state["failures"] == {}


def test_call_cap():
    caps = {**CAPS, "max_calls": 2}
    state = check_and_record(None, "a", "a", caps)
    state = check_and_record(state, "b", "b", caps)
    with pytest.raises(Refusal, match="limit 2") as refusal:
        check_and_record(state, "c", "c", caps)
    assert refusal.value.kind == "budget"


def test_signature_ignores_bash_description():
    assert signature("Bash", {"command": "ls", "description": "a"}) == signature(
        "Bash", {"command": "ls", "description": "b"}
    )
    assert signature("Bash", {"command": "ls"}) != signature("Bash", {"command": "ls -a"})


def test_run_refuses_with_exit_2_and_logs_a_receipt(project):
    assert _run(project) == (0, "")
    assert _run(project) == (0, "")
    code, err = _run(project)
    assert code == 2
    assert "AgentGuard refused Bash(npm test)" in err
    receipt = build_receipt(str(project / ".agentguard" / "claude-code" / "trace.jsonl"))
    assert receipt["tool_calls"] == 2
    assert receipt["stops"] == [{"kind": "loop", "detail": "Bash(npm test) x2, same args"}]


def test_run_counts_failures_from_post_tool_use_failure(project):
    for _ in range(2):
        assert _run(project, command="make")[0] == 0
        assert _run(project, name="PostToolUseFailure", command="make")[0] == 0
        assert _run(project, command="cat log")[0] == 0
    assert _run(project, command="make")[0] == 2


def test_sessions_are_counted_separately(project):
    _run(project)
    _run(project)
    assert _run(project, session="other")[0] == 0


def test_project_dir_env_wins_over_cwd(project, tmp_path_factory, monkeypatch):
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(elsewhere))
    _run(project)
    assert (elsewhere / ".agentguard" / "claude-code" / "state.json").exists()
    assert not (project / ".agentguard").exists()


def test_repo_config_sets_caps(project):
    (project / ".agentguard.json").write_text(json.dumps({"loop_max": 5}), encoding="utf-8")
    for _ in range(4):
        assert _run(project)[0] == 0
    assert _run(project)[0] == 2


@pytest.mark.parametrize("payload", ["not json", "[]", '{"hook_event_name": "PreToolUse"}'])
def test_unreadable_input_is_a_non_blocking_error(payload):
    stderr = io.StringIO()
    assert run(io.StringIO(payload), stderr) == 1
    assert "unreadable hook input" in stderr.getvalue()


def test_other_events_pass(project):
    assert _run(project, name="SessionStart") == (0, "")


def test_parallel_hook_processes_do_not_lose_counts(project):
    def call(i):
        payload = json.dumps(_event(project, command=f"echo {i}"))
        return subprocess.run(
            [sys.executable, "-m", "agentguard.cli", "hook", "claude-code"],
            input=payload, capture_output=True, text=True, cwd=SDK,
        ).returncode

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(call, range(8))) == [0] * 8
    state = json.loads((project / ".agentguard" / "claude-code" / "state.json").read_text())
    assert state["s1"]["calls"] == 8


def test_install_keeps_user_hooks_and_is_idempotent():
    user_hook = {"matcher": "Bash", "hooks": [{"type": "command", "command": "./lint.sh"}]}
    settings = {"model": "x", "hooks": {"PreToolUse": [user_hook]}}
    once = install_settings(json.loads(json.dumps(settings)), "/py", None)
    twice = install_settings(json.loads(json.dumps(once)), "/py", 50)
    assert twice["model"] == "x"
    assert twice["hooks"]["PreToolUse"][0] == user_hook
    assert twice["hooks"]["PreToolUse"].count(user_hook) == 1
    ours = [g for g in twice["hooks"]["PreToolUse"] if g != user_hook]
    assert len(ours) == 1
    assert ours[0]["hooks"][0]["args"][-2:] == ["--max-calls", "50"]
    assert set(twice["hooks"]) == {"PreToolUse", "PostToolUse", "PostToolUseFailure"}
    assert uninstall_settings(twice) == settings


def test_cli_install_preview_then_write(project, capsys, monkeypatch):
    from agentguard import cli

    argv = ["agentguard", "hook", "claude-code", "--install", "--project-dir", str(project)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 0
    assert "Preview of" in capsys.readouterr().out
    assert not (project / ".claude").exists()
    monkeypatch.setattr(sys, "argv", [*argv, "--write"])
    with pytest.raises(SystemExit):
        cli.main()
    written = json.loads((project / ".claude" / "settings.local.json").read_text())
    assert written["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == sys.executable


def test_hook_files_ignore_themselves_in_git(project):
    import shutil

    _run(project)
    hook_dir = project / ".agentguard" / "claude-code"
    assert (hook_dir / ".gitignore").read_text() == "*\n"
    if shutil.which("git"):
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                cwd=project, capture_output=True, text=True, check=True).stdout
        assert ".agentguard" not in status
