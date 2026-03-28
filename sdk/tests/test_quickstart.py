import ast
import io
import json
import unittest
from contextlib import redirect_stdout

from agentguard.cli import _quickstart
from agentguard.quickstart import FRAMEWORK_CHOICES, _build_quickstart_payload, run_quickstart


class TestQuickstart(unittest.TestCase):
    def test_raw_quickstart_includes_local_only_starter(self) -> None:
        buf = io.StringIO()

        result = run_quickstart(stream=buf)

        self.assertEqual(result, 0)
        output = buf.getvalue()
        self.assertIn("Framework: raw", output)
        self.assertIn("pip install agentguard47", output)
        self.assertIn("local_only=True", output)
        self.assertIn("agentguard doctor", output)

    def test_openai_quickstart_json_is_parseable(self) -> None:
        buf = io.StringIO()

        result = run_quickstart(framework="openai", json_output=True, stream=buf)

        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["framework"], "openai")
        self.assertEqual(payload["requires_env"], ["OPENAI_API_KEY"])
        self.assertIn("from openai import OpenAI", payload["snippet"])

    def test_langgraph_quickstart_is_local(self) -> None:
        buf = io.StringIO()

        result = run_quickstart(framework="langgraph", stream=buf)

        self.assertEqual(result, 0)
        output = buf.getvalue()
        self.assertIn("This example is fully local.", output)
        self.assertIn("StateGraph", output)
        self.assertIn("guard_node(", output)

    def test_invalid_framework_returns_error(self) -> None:
        buf = io.StringIO()

        result = run_quickstart(framework="unknown", json_output=True, stream=buf)

        self.assertEqual(result, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "error")
        self.assertIn("Unknown framework", payload["error"])

    def test_cli_quickstart_prints_snippet(self) -> None:
        buf = io.StringIO()

        with redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
            _quickstart(framework="anthropic")

        self.assertEqual(ctx.exception.code, 0)
        output = buf.getvalue()
        self.assertIn("Framework: anthropic", output)
        self.assertIn("ANTHROPIC_API_KEY", output)

    def test_snippets_escape_service_and_trace_file_literals(self) -> None:
        service = 'agent "alpha"\nsecond line'
        trace_file = r'traces\agent "alpha"\session.jsonl'

        for framework in FRAMEWORK_CHOICES:
            with self.subTest(framework=framework):
                payload = _build_quickstart_payload(
                    framework=framework,
                    service=service,
                    budget_usd=5.0,
                    trace_file=trace_file,
                )

                ast.parse(payload["snippet"])
                self.assertIn(json.dumps(service), payload["snippet"])
                self.assertIn(json.dumps(trace_file), payload["snippet"])


if __name__ == "__main__":
    unittest.main()
