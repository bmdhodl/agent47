"""First-run surface tests: import side effects, the welcome, the badge, CLI
dispatch for the bare command, and the ``python -m agentguard`` entry point."""

import importlib
import io
import os
import subprocess
import sys
from contextlib import redirect_stdout
from unittest import mock

import pytest

import agentguard
from agentguard import cli
from agentguard.first_run import GITHUB_REPO_URL, render_badge, render_welcome


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

        with mock.patch("pathlib.Path.home", return_value=fake_home), mock.patch.dict(
            os.environ,
            {"HOME": str(fake_home), "USERPROFILE": str(fake_home)},
            clear=False,
        ):
            _reimport_agentguard()

        assert list(fake_home.iterdir()) == []


class TestWelcome:
    def test_render_welcome_guides_to_local_path(self):
        buf = io.StringIO()
        render_welcome(stream=buf)
        out = buf.getvalue()

        assert "AgentGuard" in out
        assert "Zero dependencies" in out
        assert "agentguard doctor" in out
        assert "agentguard demo" in out
        assert "agentguard quickstart --framework raw --write" in out
        assert "agentguard --help" in out
        assert "agentguard badge" in out
        assert "python -m agentguard" in out
        assert GITHUB_REPO_URL in out

    def test_render_welcome_includes_version_when_provided(self):
        buf = io.StringIO()
        render_welcome(stream=buf, version="9.9.9")
        assert "AgentGuard 9.9.9" in buf.getvalue()


class TestBadge:
    def test_render_badge_markdown_links_back_to_repo(self):
        buf = io.StringIO()
        render_badge(stream=buf)
        out = buf.getvalue()

        assert "Guarded by AgentGuard" in out
        assert "img.shields.io/badge/guarded%20by-AgentGuard" in out
        assert GITHUB_REPO_URL in out

    def test_render_badge_rst_and_html_formats(self):
        rst = io.StringIO()
        render_badge(stream=rst, fmt="rst")
        assert ".. image::" in rst.getvalue()
        assert GITHUB_REPO_URL in rst.getvalue()

        html = io.StringIO()
        render_badge(stream=html, fmt="html")
        assert "<img" in html.getvalue()
        assert GITHUB_REPO_URL in html.getvalue()

    def test_render_badge_unknown_format_falls_back_to_markdown(self):
        buf = io.StringIO()
        render_badge(stream=buf, fmt="bogus")
        # Assert the full markdown structure (linked image), not an incidental
        # substring that would also match a badge missing its outer link wrapper.
        assert "[![Guarded by AgentGuard](" in buf.getvalue()


class TestCliDispatch:
    def _run_cli(self, argv):
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", argv), redirect_stdout(buf):
            cli.main()
        return buf.getvalue()

    def test_bare_command_shows_welcome_not_argparse_help(self):
        out = self._run_cli(["agentguard"])
        assert "Zero dependencies" in out
        assert "agentguard doctor" in out
        assert GITHUB_REPO_URL in out

    def test_welcome_subcommand(self):
        out = self._run_cli(["agentguard", "welcome"])
        assert "agentguard demo" in out

    def test_badge_subcommand_defaults_to_markdown(self):
        out = self._run_cli(["agentguard", "badge"])
        assert "[![Guarded by AgentGuard](" in out

    def test_badge_subcommand_html_format(self):
        out = self._run_cli(["agentguard", "badge", "--format", "html"])
        assert "<img" in out


_CLI_ROUTES = [
    (["agentguard"], "_welcome"),  # bare command -> welcome
    (["agentguard", "welcome"], "_welcome"),
    (["agentguard", "badge"], "_badge"),
    (["agentguard", "summarize", "t.jsonl"], "_summarize"),
    (["agentguard", "report", "t.jsonl"], "_report"),
    (["agentguard", "eval", "t.jsonl"], "_eval"),
    (["agentguard", "incident", "t.jsonl"], "_incident"),
    (["agentguard", "decisions", "t.jsonl"], "_decisions"),
    (["agentguard", "demo"], "_demo"),
    (["agentguard", "doctor"], "_doctor"),
    (["agentguard", "quickstart"], "_quickstart"),
    (["agentguard", "skillpack"], "_skillpack"),
]


class TestCliRouting:
    """Pin every dispatch branch in cli.main() so routing regressions are caught.

    main() no longer carries `# pragma: no cover`, so each subcommand must be
    exercised. Handlers are patched to keep the test fast and side-effect-free
    (several real handlers raise SystemExit and write files).
    """

    @pytest.mark.parametrize("argv,handler", _CLI_ROUTES)
    def test_main_routes_to_handler(self, argv, handler):
        with mock.patch.object(cli, handler) as patched, mock.patch.object(sys, "argv", argv):
            cli.main()
        assert patched.called, f"{argv} should route to cli.{handler}"


class TestModuleEntryPoint:
    def test_main_module_imports_cli_main(self):
        """Cover the module-level import in __main__.py and pin the wiring.

        Identity (``is``) is avoided because the autouse module-reload fixture
        gives the freshly imported entry point a distinct function object.
        """
        import agentguard.__main__ as entry

        assert callable(entry.main)
        assert entry.main.__module__ == "agentguard.cli"
        assert entry.main.__name__ == "main"

    def test_python_dash_m_agentguard_runs_cli(self):
        """`python -m agentguard` must work end-to-end (no PATH dependency)."""
        sdk_root = os.path.dirname(os.path.dirname(os.path.abspath(agentguard.__file__)))
        env = dict(os.environ)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = sdk_root + (os.pathsep + existing if existing else "")

        result = subprocess.run(
            [sys.executable, "-m", "agentguard"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr
        assert "AgentGuard" in result.stdout
        assert GITHUB_REPO_URL in result.stdout
