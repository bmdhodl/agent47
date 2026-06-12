import importlib.util
import json
import pathlib
import sys
import tempfile
import textwrap
import unittest
from subprocess import run

_SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "review_readiness_guard.py"
_SPEC = importlib.util.spec_from_file_location("review_readiness_guard", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
review_readiness_guard = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = review_readiness_guard
_SPEC.loader.exec_module(review_readiness_guard)


class TestReviewReadinessGuard(unittest.TestCase):
    def test_current_repo_is_clean(self):
        findings = review_readiness_guard.collect_findings(review_readiness_guard.REPO_ROOT)
        self.assertEqual(findings, [])

    def test_missing_pr_template_skill_gate_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".github" / "workflows").mkdir(parents=True)
            (repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
                "## Proof\n",
                encoding="utf-8",
            )
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                "\n".join(review_readiness_guard.REQUIRED_CLAUDE_REVIEW_PHRASES.values()),
                encoding="utf-8",
            )

            findings = review_readiness_guard.collect_findings(repo_root)

        self.assertTrue(any(finding.check == "pr-template:fact-ledger" for finding in findings))

    def test_workflow_full_history_and_head_pipe_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".github" / "workflows").mkdir(parents=True)
            (repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
                "\n".join(review_readiness_guard.REQUIRED_TEMPLATE_PHRASES.values()),
                encoding="utf-8",
            )
            workflow = textwrap.dedent(
                """
                uses: actions/checkout@v5
                fetch-depth: 0
                gh pr diff "$PR" | head -c 200000 > /tmp/pr.diff
                """
            )
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                workflow,
                encoding="utf-8",
            )

            findings = review_readiness_guard.collect_findings(repo_root)

        checks = {finding.check for finding in findings}
        self.assertIn("claude-review:pinned-checkout", checks)
        self.assertIn("claude-review:no-head-c", checks)
        self.assertIn("claude-review:no-full-history", checks)

    def test_json_output_is_parseable(self):
        result = run(
            [sys.executable, str(_SCRIPT_PATH), "--json"],
            capture_output=True,
            check=True,
            text=True,
            cwd=str(_SCRIPT_PATH.parents[1]),
        )

        self.assertEqual(json.loads(result.stdout), [])
