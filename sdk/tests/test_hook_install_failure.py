"""Regression coverage for fail-closed Claude Code hook installation (#871)."""
import io
import json
import shutil
import subprocess
from copy import deepcopy

import pytest

from agentguard.hooks import configure, install_settings, uninstall_settings


def _host(monkeypatch, version="2.1.295 (Claude Code)", returncode=0):
    calls = []

    def probe(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, returncode, version, "")

    monkeypatch.setattr(subprocess, "run", probe)
    monkeypatch.setattr(shutil, "which", lambda name: "/installed/claude")
    return calls


def test_pre_tool_handler_blocks_failure_and_remains_synchronous():
    installed = install_settings({}, "/py", None)
    pre = installed["hooks"]["PreToolUse"][0]["hooks"][0]
    assert pre["onFailure"] == "block"
    assert not pre.get("async")
    assert not pre.get("asyncRewake")
    for name in ("PostToolUse", "PostToolUseFailure"):
        assert "onFailure" not in installed["hooks"][name][0]["hooks"][0]


@pytest.mark.parametrize("version", ["2.1.295 (Claude Code)", "2.1.296 (Claude Code)", "3.0.0 (Claude Code)"])
def test_install_checks_supported_host_before_preview(tmp_path, monkeypatch, version):
    calls = _host(monkeypatch, version)
    output = io.StringIO()
    assert configure(str(tmp_path), False, False, None, output) == 0
    assert len(calls) == 1
    assert calls[0][0] == ["/installed/claude", "--version"]
    assert calls[0][1]["timeout"] > 0
    assert not calls[0][1].get("shell", False)
    assert "onFailure" in output.getvalue()
    assert version.split()[0] in output.getvalue()
    assert not (tmp_path / ".claude").exists()


def test_windows_npm_wrapper_path_is_resolved_before_version_probe(tmp_path, monkeypatch):
    calls = _host(monkeypatch)
    wrapper = r"C:\Program Files\npm\claude.CMD"
    monkeypatch.setattr(shutil, "which", lambda name: wrapper if name == "claude" else None)
    assert configure(str(tmp_path), False, False, None, io.StringIO()) == 0
    assert calls[0][0] == [wrapper, "--version"]


def test_missing_host_does_not_spawn_or_change_settings(tmp_path, monkeypatch):
    calls = _host(monkeypatch)
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(SystemExit, match=r"Claude Code 2\.1\.295 or later"):
        configure(str(tmp_path), True, False, None, io.StringIO())
    assert calls == []
    assert not (tmp_path / ".claude").exists()


@pytest.mark.parametrize("version", ["2.1.294 (Claude Code)", "1.9.0 (Claude Code)", "unknown", "2.1.295-beta (Claude Code)", "2.1.296 (Other App)"])
@pytest.mark.parametrize("write", [False, True])
def test_unsupported_or_unknown_host_does_not_change_settings(tmp_path, monkeypatch, version, write):
    _host(monkeypatch, version)
    path = tmp_path / ".claude" / "settings.local.json"
    path.parent.mkdir()
    original = '{ "model": "untouched", "hooks": {} }\n'
    path.write_text(original, encoding="utf-8")
    with pytest.raises(SystemExit, match=r"Claude Code 2\.1\.295 or later"):
        configure(str(tmp_path), write, False, None, io.StringIO())
    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("error", [FileNotFoundError("missing"), subprocess.TimeoutExpired(["claude", "--version"], 5)])
def test_failed_version_probe_does_not_create_settings(tmp_path, monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(shutil, "which", lambda name: "/installed/claude")
    with pytest.raises(SystemExit, match=r"Claude Code 2\.1\.295 or later"):
        configure(str(tmp_path), True, False, None, io.StringIO())
    assert not (tmp_path / ".claude").exists()


def test_nonzero_probe_does_not_trust_version_output(tmp_path, monkeypatch):
    _host(monkeypatch, returncode=1)
    with pytest.raises(SystemExit, match=r"Claude Code 2\.1\.295 or later"):
        configure(str(tmp_path), True, False, None, io.StringIO())
    assert not (tmp_path / ".claude").exists()


def test_reinstall_and_uninstall_preserve_all_unrelated_handlers_and_settings(tmp_path, monkeypatch):
    calls = _host(monkeypatch)
    settings = {
        "model": "untouched",
        "hooks": {
            "PreToolUse": [
                {"matcher": "Read", "hooks": []},
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "lint", "onFailure": "continue"}]},
            ],
            "SessionStart": [{"matcher": "*", "hooks": []}],
        },
    }
    installed = install_settings(deepcopy(settings), "/py", 1)
    # Preserve a user handler that shares a matcher group with our handler.
    shared = {"type": "command", "command": "after-policy"}
    installed["hooks"]["PreToolUse"][-1]["hooks"].append(shared)
    expected = deepcopy(settings)
    expected["hooks"]["PreToolUse"].append({"matcher": "*", "hooks": [shared]})
    assert uninstall_settings(deepcopy(installed)) == expected
    reinstalled = install_settings(deepcopy(installed), "/new-py", 2)
    assert uninstall_settings(deepcopy(reinstalled)) == expected
    path = tmp_path / ".claude" / "settings.local.json"
    path.parent.mkdir()
    path.write_text(json.dumps(reinstalled), encoding="utf-8")
    assert configure(str(tmp_path), True, True, None, io.StringIO()) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == expected
    assert calls == []  # Removal must still work when Claude is unavailable.


@pytest.mark.parametrize("settings", [{"hooks": {}}, {"hooks": {"PostToolUse": []}}])
def test_uninstall_without_agentguard_does_not_normalize_user_settings(settings):
    assert uninstall_settings(deepcopy(settings)) == settings
