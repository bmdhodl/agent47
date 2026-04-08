import ast
import io
import json
import os
import tempfile
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
        self.assertIn('profile="coding-agent"', payload["snippet"])

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

    def test_default_trace_file_uses_agentguard_directory(self) -> None:
        buf = io.StringIO()

        result = run_quickstart(stream=buf)

        self.assertEqual(result, 0)
        self.assertIn(".agentguard/traces.jsonl", buf.getvalue())

    def test_write_creates_default_framework_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                buf = io.StringIO()
                result = run_quickstart(framework="raw", write_file=True, stream=buf)
                self.assertEqual(result, 0)
                self.assertTrue(os.path.exists("agentguard_raw_quickstart.py"))
                with open("agentguard_raw_quickstart.py", encoding="utf-8") as handle:
                    written = handle.read()
                self.assertIn("agentguard.init(", written)
                self.assertIn("Wrote starter: agentguard_raw_quickstart.py", buf.getvalue())
                self.assertIn("python agentguard_raw_quickstart.py", buf.getvalue())
            finally:
                os.chdir(cwd)

    def test_write_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = os.path.join(tmp, "starter.py")
            with open(destination, "w", encoding="utf-8") as handle:
                handle.write("print('keep me')\n")

            buf = io.StringIO()
            result = run_quickstart(
                framework="raw",
                write_file=True,
                output_path=destination,
                stream=buf,
            )

            self.assertEqual(result, 1)
            self.assertIn("Refusing to overwrite existing file", buf.getvalue())
            with open(destination, encoding="utf-8") as handle:
                self.assertIn("keep me", handle.read())

    def test_write_force_overwrites_custom_output_and_json_reports_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = os.path.join(tmp, "custom_starter.py")
            with open(destination, "w", encoding="utf-8") as handle:
                handle.write("old\n")

            buf = io.StringIO()
            result = run_quickstart(
                framework="langgraph",
                write_file=True,
                output_path=destination,
                force=True,
                json_output=True,
                stream=buf,
            )

            self.assertEqual(result, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["written_file"], destination.replace("\\", "/"))
            with open(destination, encoding="utf-8") as handle:
                written = handle.read()
            self.assertIn("StateGraph", written)

    def test_cli_quickstart_can_write_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = os.path.join(tmp, "agentguard_openai_quickstart.py")
            buf = io.StringIO()

            with redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
                _quickstart(
                    framework="openai",
                    write_file=True,
                    output_path=destination,
                )

            self.assertEqual(ctx.exception.code, 0)
            self.assertTrue(os.path.exists(destination))
            self.assertIn("Wrote starter:", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
