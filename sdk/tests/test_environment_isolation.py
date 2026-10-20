"""Regression coverage for SDK test environment isolation."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_regression_ambient_agentguard_settings_do_not_reach_tests(tmp_path):
    """REGRESSION: ambient settings are cleared, explicit test settings still work."""
    tests_dir = Path(__file__).resolve().parent
    (tmp_path / "conftest.py").write_text(
        (tests_dir / "conftest.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "test_probe.py").write_text(
        """
import os


def test_ambient_settings_are_absent():
    assert not [
        name for name in os.environ
        if name.startswith("AGENTGUARD_") and name != "AGENTGUARD_REQUIRE_REAL_DEPS"
    ]
    assert os.environ["AGENTGUARDIAN"] == "unrelated-setting"


def test_explicit_test_settings_work(monkeypatch):
    monkeypatch.setenv("AGENTGUARD_SERVICE", "explicit-test-service")
    assert os.environ["AGENTGUARD_SERVICE"] == "explicit-test-service"


def test_next_test_starts_clean():
    assert os.environ.get("AGENTGUARD_SERVICE") is None
""",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "AGENTGUARD_SERVICE": "ambient-service",
        "AGENTGUARD_API_KEY": "synthetic-not-a-real-key",
        "AGENTGUARD_TRACE_FILE": str(tmp_path / "ambient.jsonl"),
        "AGENTGUARD_FUTURE_SETTING": "ambient-future-setting",
        "AGENTGUARDIAN": "unrelated-setting",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONPATH": str(tests_dir.parent),
    }
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--confcutdir", str(tmp_path), "test_probe.py"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 passed" in result.stdout


def test_regression_ci_dependency_sentinel_is_preserved(tmp_path):
    """REGRESSION: missing CI dependencies must fail import instead of skip."""
    tests_dir = Path(__file__).resolve().parent
    (tmp_path / "conftest.py").write_text(
        (tests_dir / "conftest.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "test_probe.py").write_text(
        """
import pytest
from test_real_dispatch import _require


def test_missing_dependency_is_an_import_error():
    with pytest.raises(ModuleNotFoundError, match="agentguard_missing_dependency_887"):
        _require("agentguard_missing_dependency_887")
""",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "AGENTGUARD_REQUIRE_REAL_DEPS": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONPATH": os.pathsep.join((str(tests_dir), str(tests_dir.parent))),
    }
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--confcutdir", str(tmp_path), "test_probe.py"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout, result.stdout
