import importlib.util
import json
import pathlib
import sys
import tempfile
import textwrap
import unittest
from subprocess import run
from unittest.mock import Mock, patch

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_SCRIPT_PATH = _SCRIPTS_DIR / "sdk_release_guard.py"
_SPEC = importlib.util.spec_from_file_location("sdk_release_guard", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
sdk_release_guard = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = sdk_release_guard
_SPEC.loader.exec_module(sdk_release_guard)


class TestReleaseGuardHelpers(unittest.TestCase):
    def test_collect_findings_is_clean_for_current_repo(self):
        findings = sdk_release_guard.collect_findings(sdk_release_guard.REPO_ROOT)
        self.assertEqual(findings, [])

    def test_check_changelog_reports_missing_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / "sdk").mkdir()
            (repo_root / "sdk" / "pyproject.toml").write_text(
                '[project]\nversion = "9.9.9"\n',
                encoding="utf-8",
            )
            (repo_root / "CHANGELOG.md").write_text("## 9.9.8\n\nold\n", encoding="utf-8")

            findings = sdk_release_guard.check_changelog(repo_root, "9.9.9")
            self.assertEqual(len(findings), 1)
            self.assertIn("Could not find changelog section", findings[0].message)

    def test_check_release_markers_reports_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".claude" / "agents").mkdir(parents=True)
            files = {
                "AGENTS.md": textwrap.dedent(
                    """
                    latest shipped release: v0.0.1
                    latest shipped release is 0.0.1
                    """
                ),
                "CLAUDE.md": textwrap.dedent(
                    """
                    latest shipped release: v0.0.1
                    latest shipped release is 0.0.1
                    """
                ),
                ".claude/agents/sdk-dev.md": "Latest shipped SDK release: `v0.0.1`\n",
            }
            for relative_path, content in files.items():
                path = repo_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            findings = sdk_release_guard.check_release_markers(repo_root, "9.9.9")
            self.assertEqual(len(findings), len(sdk_release_guard.RELEASE_MARKERS))
            self.assertTrue(all("Expected release marker 9.9.9" in finding.message for finding in findings))

    def test_check_pypi_readme_reports_generation_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / "sdk").mkdir()
            (repo_root / "sdk" / "pyproject.toml").write_text(
                '[project]\nversion = "9.9.9"\n',
                encoding="utf-8",
            )
            (repo_root / "README.md").write_text("# Test\n", encoding="utf-8")
            (repo_root / "CHANGELOG.md").write_text("## 9.9.8\n\nold\n", encoding="utf-8")

            findings = sdk_release_guard.check_pypi_readme(repo_root)
            self.assertEqual(len(findings), 1)
            self.assertIn("Could not find changelog section", findings[0].message)

    def test_check_mcp_metadata_reports_version_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / "mcp-server" / "src").mkdir(parents=True)
            (repo_root / "mcp-server" / "package.json").write_text(
                json.dumps({"version": "0.2.2"}),
                encoding="utf-8",
            )
            (repo_root / "mcp-server" / "server.json").write_text(
                json.dumps(
                    {
                        "version": "0.2.1",
                        "packages": [{"version": "0.2.0"}],
                    }
                ),
                encoding="utf-8",
            )
            (repo_root / "mcp-server" / "src" / "index.ts").write_text(
                'const server = { version: "0.2.1" };\n',
                encoding="utf-8",
            )

            findings = sdk_release_guard.check_mcp_metadata(repo_root)
            self.assertEqual(len(findings), 3)
            self.assertTrue(all(finding.check == "mcp-metadata" for finding in findings))

    def test_check_mcp_npm_package_reports_unpublished_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / "mcp-server").mkdir()
            (repo_root / "mcp-server" / "package.json").write_text(
                json.dumps(
                    {
                        "name": "@agentguard47/mcp-server",
                        "version": "0.2.2",
                    }
                ),
                encoding="utf-8",
            )

            failed = Mock(returncode=1, stdout="", stderr="E404 not found")
            with patch.object(sdk_release_guard.subprocess, "run", return_value=failed) as npm_view:
                findings = sdk_release_guard.check_mcp_npm_package(repo_root, npm_command="npm")

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].check, "mcp-npm")
            self.assertIn("Expected @agentguard47/mcp-server@0.2.2", findings[0].message)
            npm_view.assert_called_once_with(
                ["npm", "view", "@agentguard47/mcp-server@0.2.2", "version"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_check_mcp_npm_package_reports_latest_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / "mcp-server").mkdir()
            (repo_root / "mcp-server" / "package.json").write_text(
                json.dumps(
                    {
                        "name": "@agentguard47/mcp-server",
                        "version": "0.2.2",
                    }
                ),
                encoding="utf-8",
            )

            exact = Mock(returncode=0, stdout="0.2.2\n", stderr="")
            latest = Mock(returncode=0, stdout="0.2.1\n", stderr="")
            with patch.object(sdk_release_guard.subprocess, "run", side_effect=[exact, latest]):
                findings = sdk_release_guard.check_mcp_npm_package(repo_root, npm_command="npm")

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].check, "mcp-npm")
            self.assertIn("Expected npm latest 0.2.2, found 0.2.1", findings[0].message)


class TestReleaseGuardCli(unittest.TestCase):
    def test_json_output_is_parseable(self):
        result = run(
            [sys.executable, str(_SCRIPT_PATH), "--json"],
            capture_output=True,
            check=True,
            text=True,
            cwd=str(_SCRIPT_PATH.parents[1]),
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload, [])
