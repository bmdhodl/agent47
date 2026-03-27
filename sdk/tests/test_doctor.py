import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from agentguard.cli import _doctor
from agentguard.doctor import run_doctor


class TestDoctor(unittest.TestCase):
    def test_run_doctor_writes_local_trace_and_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "doctor.jsonl")
            buf = io.StringIO()

            result = run_doctor(trace_path=trace_path, stream=buf)

            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists(trace_path))
            output = buf.getvalue()
            self.assertIn("No dashboard. No network calls. Local verification only.", output)
            self.assertIn("Suggested next step:", output)
            self.assertIn("local_only=True", output)
            self.assertIn("agentguard demo", output)

    def test_run_doctor_json_output_is_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "doctor.jsonl")
            buf = io.StringIO()

            result = run_doctor(trace_path=trace_path, stream=buf, json_output=True)

            self.assertEqual(result, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["trace_file"], trace_path)
            self.assertGreaterEqual(payload["events_written"], 4)
            self.assertIn("recommended_snippet", payload)

    def test_run_doctor_ignores_api_key_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "doctor.jsonl")
            buf = io.StringIO()

            with patch.dict(os.environ, {"AGENTGUARD_API_KEY": "ag_should_be_ignored"}):
                result = run_doctor(trace_path=trace_path, stream=buf)

            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists(trace_path))

    def test_detected_integrations_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "doctor.jsonl")
            buf = io.StringIO()

            def fake_find_spec(name: str):
                if name in {"openai", "langchain_core"}:
                    return object()
                return None

            with patch("agentguard.doctor.importlib.util.find_spec", side_effect=fake_find_spec):
                result = run_doctor(trace_path=trace_path, stream=buf, json_output=True)

            self.assertEqual(result, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["detected_integrations"], ["openai", "langchain"])

    def test_cli_doctor_writes_trace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "doctor.jsonl")
            buf = io.StringIO()

            with redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
                _doctor(trace_path=trace_path)

            self.assertEqual(ctx.exception.code, 0)
            self.assertTrue(os.path.exists(trace_path))
            self.assertIn("AgentGuard doctor", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
