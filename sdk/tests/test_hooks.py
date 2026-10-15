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


def _event(project, name="PreToolUse", command="npm test", session="s1", tool="Bash",
           tool_input=None, **extra):
    return {
        "session_id": session,
        "hook_event_name": name,
        "cwd": str(project),
        "tool_name": tool,
        "tool_input": tool_input or {"command": command, "description": "run it"},
        **extra,
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
    assert "AgentGuard refused Bash:" in err
    receipt = build_receipt(str(project / ".agentguard" / "claude-code" / "trace.jsonl"))
    assert receipt["tool_calls"] == 2
    assert receipt["stops"] == [{"kind": "loop", "detail":
                                 'Bash x2, same args'}]


def test_signature_ignores_key_order_but_preserves_case_and_whitespace():
    assert signature("Grep", {"pattern": "retryCount", "path": "src"}) == signature(
        "Grep", {"path": "src", "pattern": "retryCount"}
    )
    assert signature("Grep", {"pattern": "retry count"}) != signature("Grep", {"pattern": "retry\tcount"})
    assert signature("Grep", {"pattern": "retry_count"}) != signature("Grep", {"pattern": "retryCount2"})


def test_run_preserves_command_case_and_whitespace(project):
    assert _run(project, command="npm test")[0] == 0
    assert _run(project, command="npm  test ")[0] == 0
    code, err = _run(project, command="NPM test")
    assert (code, err) == (0, "")


def _grep(project, pattern, name="PreToolUse", **extra):
    stderr = io.StringIO()
    payload = _event(project, name=name, tool="Grep", tool_input={"pattern": pattern}, **extra)
    return run(io.StringIO(json.dumps(payload)), stderr), stderr.getvalue()


NO_MATCHES = {"mode": "files_with_matches", "filenames": [], "numFiles": 0}


def test_run_refuses_reworded_searches_that_keep_coming_back_empty(project):
    (project / ".agentguard.json").write_text('{"no_progress_max": 5}', encoding="utf-8")
    patterns = ["retry_count", "retryCount", "retries", "max_retry", "RETRY_LIMIT"]
    for pattern in patterns:
        assert _grep(project, pattern) == (0, "")
        assert _grep(project, pattern, name="PostToolUse", tool_response=NO_MATCHES)[0] == 0
    code, err = _grep(project, "retry_max")
    assert code == 2
    assert "Grep came back empty the last 5 times in a row" in err
    receipt = build_receipt(str(project / ".agentguard" / "claude-code" / "trace.jsonl"))
    assert receipt["stops"] == [{"kind": "loop", "detail":
                                 'Grep: empty x5, input varied'}]
    # Another tool's result ends the run, so the agent can change approach.
    assert _run(project, command="ls src")[0] == 0
    assert _run(project, name="PostToolUse", command="ls src", tool_response={"stdout": "a.py"})[0] == 0
    assert _grep(project, "retry_max")[0] == 0


def test_run_refuses_reworded_commands_failing_with_the_same_error(project):
    (project / ".agentguard.json").write_text('{"no_progress_max": 5}', encoding="utf-8")
    for path in ["a.log", "b.log", "c.log", "logs/d.log", "logs/e.log"]:
        assert _run(project, command=f"cat {path}")[0] == 0
        assert _run(project, name="PostToolUseFailure", command=f"cat {path}",
                    error=f"Exit code 1\ncat: {path}: No such file or directory")[0] == 0
    code, err = _run(project, command="cat f.log")
    assert code == 2
    assert "Bash failed with the same error the last 5 times" in err


def test_edit_and_test_cycle_with_failing_tests_is_not_refused(project):
    # retry_max separately refuses an unchanged command that already failed; isolate no-progress.
    (project / ".agentguard.json").write_text(json.dumps({"retry_max": 100}), encoding="utf-8")
    for attempt in range(8):
        assert _run(project, command="pytest -q")[0] == 0
        assert _run(project, name="PostToolUseFailure", command="pytest -q",
                    error="Exit code 1\n1 failed in 0.4s")[0] == 0
        edit = {"file_path": "app.py", "old_string": f"v{attempt}", "new_string": f"v{attempt + 1}"}
        stderr = io.StringIO()
        for name, more in (("PreToolUse", {}), ("PostToolUse", {"tool_response": {"filePath": "app.py"}})):
            payload = _event(project, name=name, tool="Edit", tool_input=edit, **more)
            assert run(io.StringIO(json.dumps(payload)), stderr) == 0


def test_quiet_successes_and_pagination_are_progress(project):
    for i in range(12):
        assert _run(project, command=f"mkdir -p out/{i}")[0] == 0
        assert _run(project, name="PostToolUse", command=f"mkdir -p out/{i}",
                    tool_response={"stdout": "", "stderr": "", "interrupted": False})[0] == 0
    for page in range(12):
        fetch = {"url": f"https://api.example.com/items?page={page}"}
        for name, more in (("PreToolUse", {}), ("PostToolUse", {"tool_response": {"result": f"item {page}"}})):
            payload = _event(project, name=name, tool="WebFetch", tool_input=fetch, **more)
            assert run(io.StringIO(json.dumps(payload)), io.StringIO()) == 0


def test_interrupts_and_missing_responses_do_not_count(project):
    for pattern in ["a1", "b2", "c3", "d4", "e5", "f6"]:
        assert _grep(project, pattern)[0] == 0
        assert _grep(project, pattern, name="PostToolUseFailure", error="interrupted",
                     is_interrupt=True)[0] == 0
        assert _grep(project, pattern, name="PostToolUse")[0] == 0
    assert _grep(project, "g7")[0] == 0


def test_repo_config_can_turn_no_progress_off(project):
    (project / ".agentguard.json").write_text(json.dumps({"no_progress_max": 0}), encoding="utf-8")
    for pattern in ["a1", "b2", "c3", "d4", "e5", "f6", "g7"]:
        assert _grep(project, pattern)[0] == 0
        assert _grep(project, pattern, name="PostToolUse", tool_response=NO_MATCHES)[0] == 0


def test_state_files_from_before_no_progress_still_load():
    old = {"calls": 3, "last": "x", "streak": 1, "failures": {}}
    state = check_and_record(dict(old), "y", "Grep(y)", {**CAPS, "no_progress_max": 5}, "Grep", {})
    assert state["calls"] == 4
    state = record_result(state, "y", failed=False, tool="Grep", outcome="empty")
    assert state["stall"] == {"tool": "Grep", "outcome": "empty", "count": 1}


def test_refusal_data_omits_arbitrary_input_keys_and_values():
    state = check_and_record(None, "a", "Bash", CAPS, "Bash", {"private-key": "private-value"})
    state = check_and_record(state, "a", "Bash", CAPS, "Bash", {"private-key": "private-value"})
    with pytest.raises(Refusal) as refusal:
        check_and_record(state, "a", "Bash", CAPS, "Bash", {"private-key": "private-value"})
    assert refusal.value.data == {"tool_name": "Bash", "repeats": 2, "limit": 2}


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
    assert (elsewhere / ".agentguard" / "claude-code" / "sessions" / "s1.json").exists()
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
    state = json.loads((project / ".agentguard" / "claude-code" / "sessions" / "s1.json").read_text())
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


def test_uninstall_keeps_user_hooks_that_mention_agentguard():
    lookalike = {"type": "command", "command": "python",
                 "args": ["-m", "mylinter", "agentguard.cli", "claude-code"]}
    settings = {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [lookalike]}]}}
    installed = install_settings(json.loads(json.dumps(settings)), "/py", 10)
    assert uninstall_settings(installed) == settings


def test_install_refuses_invalid_settings_without_overwriting(project):
    from agentguard.hooks import configure

    settings = project / ".claude" / "settings.local.json"
    settings.parent.mkdir()
    settings.write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit, match="not valid JSON"):
        configure(str(project), True, False, None, io.StringIO())
    assert settings.read_text(encoding="utf-8") == "{not json"


def test_install_and_uninstall_together_is_an_error(monkeypatch):
    from agentguard import cli

    monkeypatch.setattr(sys, "argv", ["agentguard", "hook", "claude-code", "--install", "--uninstall"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 2
