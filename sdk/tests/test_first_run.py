"""Tests that importing agentguard has no user-visible side effects."""

import importlib
import sys
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def _clean_module():
    """Remove agentguard from sys.modules so re-import exercises import-time behavior."""
    mods = [k for k in sys.modules if k == "agentguard" or k.startswith("agentguard.")]
    saved = {k: sys.modules.pop(k) for k in mods}
    yield
    sys.modules.update(saved)


def _reimport_agentguard():
    """Re-import agentguard and return the module."""
    import agentguard

    importlib.reload(agentguard)
    return agentguard


class TestImportSideEffects:
    def test_import_is_silent(self, capsys):
        _reimport_agentguard()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_import_does_not_touch_home_directory(self, tmp_path):
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with mock.patch("pathlib.Path.home", return_value=fake_home):
            _reimport_agentguard()

        assert list(fake_home.iterdir()) == []
