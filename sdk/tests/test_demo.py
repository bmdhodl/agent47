import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from agentguard.cli import _demo
from agentguard.demo import run_offline_demo


class TestOfflineDemo(unittest.TestCase):
    def test_run_offline_demo_writes_trace_and_explains_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "demo.jsonl")
            buf = io.StringIO()

            result = run_offline_demo(trace_path=trace_path, stream=buf)

            self.assertEqual(result, 0)
            output = buf.getvalue()
            self.assertIn("No API keys. No dashboard. No network calls.", output)
            self.assertIn("BudgetGuard", output)
            self.assertIn("LoopGuard", output)
            self.assertIn("RetryGuard", output)
            self.assertIn("SDK gives you local enforcement. The dashboard adds alerts", output)
            self.assertTrue(os.path.exists(trace_path))

            with open(trace_path, encoding="utf-8") as handle:
                events = [json.loads(line) for line in handle if line.strip()]

            names = [event["name"] for event in events]
            self.assertIn("guard.budget_exceeded", names)
            self.assertIn("guard.loop_detected", names)
            self.assertIn("guard.retry_limit_exceeded", names)

    def test_cli_demo_writes_trace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = os.path.join(tmpdir, "cli_demo.jsonl")
            buf = io.StringIO()

            with redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
                _demo(trace_path=trace_path)

            self.assertEqual(ctx.exception.code, 0)
            self.assertTrue(os.path.exists(trace_path))
            self.assertIn("Trace written to", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
