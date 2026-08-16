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

    def test_workflow_requires_semantic_three_hundred_second_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".github" / "workflows").mkdir(parents=True)
            (repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
                "\n".join(review_readiness_guard.REQUIRED_TEMPLATE_PHRASES.values()),
                encoding="utf-8",
            )
            workflow = "\n".join(review_readiness_guard.REQUIRED_CLAUDE_REVIEW_PHRASES.values())
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                workflow,
                encoding="utf-8",
            )
            (repo_root / ".github" / "claude-review").mkdir(parents=True)
            (repo_root / ".github" / "claude-review" / "package.json").write_text(
                json.dumps(
                    {"dependencies": {"@anthropic-ai/claude-code": "2.1.175"}}
                ),
                encoding="utf-8",
            )
            (repo_root / ".github" / "claude-review" / "package-lock.json").write_text(
                json.dumps(
                    {
                        "packages": {
                            "": {"dependencies": {"@anthropic-ai/claude-code": "2.1.175"}},
                            "node_modules/@anthropic-ai/claude-code": {"version": "2.1.175"},
                        }
                    }
                ),
                encoding="utf-8",
            )

            findings = review_readiness_guard.collect_findings(repo_root)

        self.assertIn("claude-review:claude-timeout", {finding.check for finding in findings})

    def test_workflow_requires_trusted_base_for_runtime_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".github" / "workflows").mkdir(parents=True)
            (repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
                "\n".join(review_readiness_guard.REQUIRED_TEMPLATE_PHRASES.values()),
                encoding="utf-8",
            )
            workflow = "\n".join(review_readiness_guard.REQUIRED_CLAUDE_REVIEW_PHRASES.values())
            workflow += "\ntimeout 300s .github/claude-review/node_modules/.bin/claude -p --output-format text"
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                workflow,
                encoding="utf-8",
            )
            (repo_root / ".github" / "claude-review").mkdir(parents=True)
            (repo_root / ".github" / "claude-review" / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {"@anthropic-ai/claude-code": "2.1.175"},
                        "scripts": {"postinstall": "node replace-claude-bin.js"},
                        "bin": {"claude": "replace-claude-bin.js"},
                    }
                ),
                encoding="utf-8",
            )
            (repo_root / ".github" / "claude-review" / "package-lock.json").write_text(
                json.dumps(
                    {
                        "packages": {
                            "": {"dependencies": {"@anthropic-ai/claude-code": "2.1.175"}},
                            "node_modules/@anthropic-ai/claude-code": {"version": "2.1.175"},
                            "node_modules/evil-claude-bin": {
                                "version": "1.0.0",
                                "bin": {"claude": "replace-claude-bin.js"},
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )

            untrusted_workflow = workflow.replace("pull_request_target:", "pull_request:")
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                untrusted_workflow,
                encoding="utf-8",
            )
            findings = review_readiness_guard.collect_findings(repo_root)

        checks = {finding.check for finding in findings}
        self.assertIn("claude-review:trusted-trigger", checks)

    def test_timeout_must_anchor_local_cli_immediately_after_duration(self):
        valid = (
            "timeout 300s "
            ".github/claude-review/node_modules/.bin/claude -p --output-format text"
        )
        pipeline_valid = (
            "} | timeout 300s "
            ".github/claude-review/node_modules/.bin/claude -p --output-format text"
        )
        false_positive = (
            "timeout 300s true && "
            ".github/claude-review/node_modules/.bin/claude -p --output-format text"
        )

        self.assertIsNotNone(review_readiness_guard.CLAUDE_TIMEOUT_PATTERN.search(valid))
        self.assertIsNotNone(
            review_readiness_guard.CLAUDE_TIMEOUT_PATTERN.search(pipeline_valid)
        )
        self.assertIsNone(review_readiness_guard.CLAUDE_TIMEOUT_PATTERN.search(false_positive))

    def test_timeout_rejects_inert_prefixes(self):
        cli_command = (
            "timeout 300s "
            ".github/claude-review/node_modules/.bin/claude -p --output-format text"
        )

        for inert_prefix in ("echo ", "false && ", "diagnostic "):
            with self.subTest(inert_prefix=inert_prefix):
                self.assertIsNone(
                    review_readiness_guard.CLAUDE_TIMEOUT_PATTERN.search(
                        inert_prefix + cli_command
                    )
                )

    def test_lockfile_backed_cli_contract_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            (repo_root / ".github" / "workflows").mkdir(parents=True)
            (repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
                "\n".join(review_readiness_guard.REQUIRED_TEMPLATE_PHRASES.values()),
                encoding="utf-8",
            )
            workflow = "\n".join(review_readiness_guard.REQUIRED_CLAUDE_REVIEW_PHRASES.values())
            workflow += "\ntimeout 300s .github/claude-review/node_modules/.bin/claude -p --output-format text"
            (repo_root / ".github" / "workflows" / "claude-review.yml").write_text(
                workflow,
                encoding="utf-8",
            )

            findings = review_readiness_guard.collect_findings(repo_root)

        checks = {finding.check for finding in findings}
        self.assertIn("claude-review:package-manifest", checks)
        self.assertIn("claude-review:lockfile", checks)

    def test_json_output_is_parseable(self):
        result = run(
            [sys.executable, str(_SCRIPT_PATH), "--json"],
            capture_output=True,
            check=True,
            text=True,
            cwd=str(_SCRIPT_PATH.parents[1]),
        )

        self.assertEqual(json.loads(result.stdout), [])
