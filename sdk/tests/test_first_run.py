"""Tests for the first-run star prompt."""
import importlib
import os
import sys
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def _clean_module():
    """Remove agentguard from sys.modules so re-import triggers first-run."""
    # Remove all agentguard modules to force re-import
    mods = [k for k in sys.modules if k == "agentguard" or k.startswith("agentguard.")]
    saved = {k: sys.modules.pop(k) for k in mods}
    yield
    # Restore
    sys.modules.update(saved)


@pytest.fixture
def tmp_home(tmp_path):
    """Provide a temporary home directory."""
    return tmp_path


def _reimport_agentguard(home_dir, env_overrides=None):
    """Re-import agentguard with a custom HOME and optional env vars."""
    env = os.environ.copy()
    # Clear all CI env vars
    for v in ("CI", "GITHUB_ACTIONS", "JENKINS_URL", "GITLAB_CI",
              "CIRCLECI", "TRAVIS", "TF_BUILD", "BUILDKITE"):
        env.pop(v, None)
    env.pop("AGENTGUARD_QUIET", None)
    env["HOME"] = str(home_dir)
    if env_overrides:
        env.update(env_overrides)
    with mock.patch.dict(os.environ, env, clear=True):
        with mock.patch("pathlib.Path.home", return_value=home_dir):
            import agentguard
            importlib.reload(agentguard)
            return agentguard


class TestFirstRun:
    def test_first_run_shows_message(self, tmp_home, capsys):
        _reimport_agentguard(tmp_home)
        captured = capsys.readouterr()
        assert "agentguard47" in captured.err
        assert "Star us" in captured.err
        assert "github.com/bmdhodl/agent47" in captured.err

    def test_second_run_suppressed(self, tmp_home, capsys):
        _reimport_agentguard(tmp_home)
        capsys.readouterr()  # consume first run output

        # Remove from sys.modules and re-import
        mods = [k for k in sys.modules if k == "agentguard" or k.startswith("agentguard.")]
        for k in mods:
            del sys.modules[k]
        _reimport_agentguard(tmp_home)
        captured = capsys.readouterr()
        assert "Star us" not in captured.err

    def test_marker_file_created(self, tmp_home):
        _reimport_agentguard(tmp_home)
        marker = tmp_home / ".agentguard" / ".first_run_shown"
        assert marker.exists()

    def test_quiet_env_suppresses(self, tmp_home, capsys):
        _reimport_agentguard(tmp_home, {"AGENTGUARD_QUIET": "1"})
        captured = capsys.readouterr()
        assert "Star us" not in captured.err
        marker = tmp_home / ".agentguard" / ".first_run_shown"
        assert not marker.exists()


class TestCIDetection:
    @pytest.mark.parametrize("ci_var", [
        "CI", "GITHUB_ACTIONS", "JENKINS_URL", "GITLAB_CI",
        "CIRCLECI", "TRAVIS", "TF_BUILD", "BUILDKITE",
    ])
    def test_ci_env_suppresses(self, tmp_home, capsys, ci_var):
        _reimport_agentguard(tmp_home, {ci_var: "true"})
        captured = capsys.readouterr()
        assert "Star us" not in captured.err
        marker = tmp_home / ".agentguard" / ".first_run_shown"
        assert not marker.exists()


class TestEdgeCases:
    def test_missing_home_dir_no_crash(self, capsys):
        """If home dir doesn't exist, should not crash."""
        fake_home = Path("/nonexistent/path/that/does/not/exist")
        _reimport_agentguard(fake_home)
        # Should not raise — failure is silently caught

    def test_readonly_home_dir_no_crash(self, tmp_home, capsys):
        """If we can't write the marker, should not crash."""
        ag_dir = tmp_home / ".agentguard"
        ag_dir.mkdir()
        ag_dir.chmod(0o444)
        try:
            _reimport_agentguard(tmp_home)
            # Should not raise
        finally:
            ag_dir.chmod(0o755)
