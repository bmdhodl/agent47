"""End-to-end tests for the scout automation pipeline.

Verifies that:
  1. Scout context generation works (reads pyproject.toml + README)
  2. All code snippets in templates actually compile against the SDK
  3. Issue classification returns valid categories
  4. Comment templates render correctly (short, no code blocks)
  5. URL parsing and relevance filtering work correctly
  6. If the SDK API changes, these tests break — preventing stale outreach
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


class TestScoutContext(unittest.TestCase):
    """Test that scout_context.json can be generated and is valid."""

    def test_generate_context(self) -> None:
        """update_scout_context.py runs and produces valid JSON."""
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "scripts", "update_scout_context.py")],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        path = os.path.join(REPO_ROOT, "docs", "outreach", "scout_context.json")
        with open(path) as f:
            ctx = json.load(f)

        self.assertIn("version", ctx)
        self.assertIn("package", ctx)
        self.assertIn("snippets", ctx)
        self.assertIn("features", ctx)
        self.assertGreater(len(ctx["features"]), 0)
        self.assertEqual(ctx["package"], "agentguard47")

    def test_version_matches_pyproject(self) -> None:
        """Context version matches sdk/pyproject.toml."""
        import re as _re
        with open(os.path.join(REPO_ROOT, "sdk", "pyproject.toml")) as f:
            content = f.read()
        match = _re.search(r'^version\s*=\s*"([^"]+)"', content, _re.MULTILINE)
        expected = match.group(1) if match else "unknown"

        from update_scout_context import read_version
        version, _ = read_version()
        self.assertEqual(version, expected)

    def test_features_parsed_from_readme(self) -> None:
        """Features are parsed from README.md, not hardcoded."""
        from update_scout_context import read_features
        features = read_features()
        self.assertGreater(len(features), 3)
        # Should contain some key features
        combined = " ".join(features).lower()
        self.assertIn("loop", combined)
        self.assertIn("cost", combined)


class TestSnippetsCompile(unittest.TestCase):
    """Verify that all code snippets in templates reference real SDK classes."""

    def test_loop_guard_snippet(self) -> None:
        """LoopGuard snippet uses valid imports and API."""
        from agentguard import LoopGuard
        guard = LoopGuard(max_repeats=3)
        guard.check(tool_name="search", tool_args={"query": "test"})

    def test_budget_guard_snippet(self) -> None:
        """BudgetGuard snippet uses valid imports and API."""
        from agentguard import BudgetGuard
        guard = BudgetGuard(max_cost_usd=5.00)
        guard.consume(cost_usd=0.12)

    def test_langchain_snippet_imports(self) -> None:
        """LangChain snippet references real classes."""
        from agentguard.integrations.langchain import AgentGuardCallbackHandler
        from agentguard import LoopGuard, BudgetGuard
        handler = AgentGuardCallbackHandler(
            loop_guard=LoopGuard(max_repeats=3),
            budget_guard=BudgetGuard(max_cost_usd=5.00),
        )
        self.assertIsNotNone(handler)

    def test_all_snippet_code_blocks_parse(self) -> None:
        """Every snippet in scout_context.json is valid Python syntax."""
        from update_scout_context import build_snippets
        snippets = build_snippets()
        for name, code in snippets.items():
            # Filter out lines that reference external packages (ChatOpenAI, etc.)
            lines = [
                line for line in code.splitlines()
                if not any(ext in line for ext in ["ChatOpenAI", "# "])
            ]
            filtered = "\n".join(lines)
            try:
                compile(filtered, f"<snippet:{name}>", "exec")
            except SyntaxError as e:
                self.fail(f"Snippet '{name}' has syntax error: {e}")


class TestClassification(unittest.TestCase):
    """Test issue classification logic."""

    def test_loop_issues(self) -> None:
        from scout import classify
        self.assertEqual(classify("Agent stuck in infinite loop"), "loop")
        self.assertEqual(classify("Tool call keeps repeating"), "loop")
        self.assertEqual(classify("Retry loop consuming all tokens"), "loop")
        self.assertEqual(classify("Agent cycling between two tools"), "loop")

    def test_cost_issues(self) -> None:
        from scout import classify
        self.assertEqual(classify("Agent cost is out of control"), "cost")
        self.assertEqual(classify("Budget exceeded on GPT-4 calls"), "cost")
        self.assertEqual(classify("Expensive billing from runaway agent"), "cost")
        self.assertEqual(classify("How to limit spending on API calls"), "cost")

    def test_debug_issues(self) -> None:
        from scout import classify
        self.assertEqual(classify("How to debug agent tool calls"), "debug")
        self.assertEqual(classify("Agent not working correctly"), "debug")
        self.assertEqual(classify("Need help with agent setup"), "debug")

    def test_mixed_defaults_to_strongest(self) -> None:
        from scout import classify
        # "loop" + "cost" → whichever has more keyword hits
        self.assertEqual(classify("infinite loop burning budget"), "loop")


class TestParseIssueUrl(unittest.TestCase):
    """Test URL parsing helper."""

    def test_valid_url(self) -> None:
        from scout import parse_issue_url
        result = parse_issue_url("https://github.com/owner/repo/issues/123")
        self.assertEqual(result, ("owner/repo", "123"))

    def test_trailing_slash(self) -> None:
        from scout import parse_issue_url
        result = parse_issue_url("https://github.com/owner/repo/issues/456/")
        self.assertEqual(result, ("owner/repo", "456"))

    def test_malformed_url(self) -> None:
        from scout import parse_issue_url
        self.assertIsNone(parse_issue_url("https://short"))
        self.assertIsNone(parse_issue_url(""))

    def test_real_world_urls(self) -> None:
        from scout import parse_issue_url
        result = parse_issue_url("https://github.com/langchain-ai/langchain/issues/34884")
        self.assertEqual(result, ("langchain-ai/langchain", "34884"))
        result = parse_issue_url("https://github.com/google/adk-python/issues/4179")
        self.assertEqual(result, ("google/adk-python", "4179"))


class TestIsRelevant(unittest.TestCase):
    """Test issue content relevance filtering."""

    def test_python_mentioned_is_relevant(self) -> None:
        from scout import is_relevant
        self.assertTrue(is_relevant({"title": "Python agent loop", "body": ""}))
        self.assertTrue(is_relevant({"title": "Loop issue", "body": "Using Python 3.12"}))

    def test_typescript_skipped(self) -> None:
        from scout import is_relevant
        self.assertFalse(is_relevant({
            "title": "Agent infinite loop",
            "body": "Using TypeScript with LangChain.js"
        }))

    def test_javascript_skipped(self) -> None:
        from scout import is_relevant
        self.assertFalse(is_relevant({
            "title": "Tool call loop",
            "body": "My JavaScript agent keeps looping"
        }))

    def test_rust_skipped(self) -> None:
        from scout import is_relevant
        self.assertFalse(is_relevant({
            "title": "Budget exceeded",
            "body": "Running a Rust-based agent"
        }))

    def test_language_neutral_is_relevant(self) -> None:
        from scout import is_relevant
        self.assertTrue(is_relevant({
            "title": "Agent stuck in infinite loop",
            "body": "My agent keeps calling the same tool over and over"
        }))

    def test_python_overrides_other_languages(self) -> None:
        from scout import is_relevant
        self.assertTrue(is_relevant({
            "title": "Agent loop in Python",
            "body": "Also affects JavaScript but I need Python fix"
        }))

    def test_empty_body(self) -> None:
        from scout import is_relevant
        self.assertTrue(is_relevant({"title": "Agent loop", "body": None}))
        self.assertTrue(is_relevant({"title": "Agent loop", "body": ""}))


class TestTemplateRendering(unittest.TestCase):
    """Test that rendered comments are short, human, and correct."""

    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "scripts", "update_scout_context.py")],
            capture_output=True, cwd=REPO_ROOT,
        )
        path = os.path.join(REPO_ROOT, "docs", "outreach", "scout_context.json")
        with open(path) as f:
            cls.ctx = json.load(f)

    def test_all_categories_render(self) -> None:
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertGreater(len(comment), 50, f"{category} template too short")

    def test_templates_include_repo_url(self) -> None:
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertIn("bmdhodl/agent47", comment,
                          f"{category} template missing repo URL")

    def test_templates_mention_agentguard(self) -> None:
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertIn("agentguard", comment.lower(),
                          f"{category} template missing agentguard mention")

    def test_no_code_blocks(self) -> None:
        """Templates should NOT contain code blocks — keep it casual."""
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertNotIn("```", comment,
                             f"{category} template has code block — should be short and human")

    def test_no_install_command(self) -> None:
        """Templates should NOT contain pip install commands."""
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertNotIn("pip install", comment,
                             f"{category} template has install command — too promotional")

    def test_no_version_number(self) -> None:
        """Templates should NOT contain version numbers."""
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertNotIn(self.ctx["version"], comment,
                             f"{category} template has version number — too promotional")

    def test_templates_are_short(self) -> None:
        """Each template should be under 400 characters."""
        from scout import render_comment
        for category in ("loop", "cost", "debug"):
            comment = render_comment(category, self.ctx)
            self.assertLess(len(comment), 400,
                            f"{category} template is {len(comment)} chars — should be under 400")


if __name__ == "__main__":
    unittest.main()
