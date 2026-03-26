import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import agentguard.cli as cli


class TestCliReport(unittest.TestCase):
    def test_report_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "service": "demo",
                    "kind": "span",
                    "phase": "end",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "agent.run",
                    "ts": 0,
                    "duration_ms": 10.0,
                    "data": {},
                    "error": None,
                },
                {
                    "service": "demo",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "reasoning.step",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {},
                    "error": None,
                },
            ]
            with open(path, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._report(path)

            output = buf.getvalue()
            self.assertIn("AgentGuard report", output)
            self.assertIn("Reasoning steps: 1", output)
            self.assertIn("Approx run time", output)
            self.assertIn("Estimated cost: $0.00", output)

    def test_report_with_cost(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "service": "demo",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "llm.result",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {"cost_usd": 0.0075},
                    "error": None,
                },
                {
                    "service": "demo",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "llm.result",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {"cost_usd": 0.015},
                    "error": None,
                },
            ]
            with open(path, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._report(path)

            output = buf.getvalue()
            self.assertIn("Estimated cost: $0.0225", output)

    def test_report_markdown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "service": "demo",
                    "kind": "span",
                    "phase": "end",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "agent.run",
                    "ts": 0,
                    "duration_ms": 10.0,
                    "cost_usd": 1.0,
                    "data": {},
                    "error": None,
                },
                {
                    "service": "demo",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "span_id": "s1",
                    "parent_id": None,
                    "name": "guard.loop_detected",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {"message": "Loop detected"},
                    "error": None,
                },
            ]
            with open(path, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._report(path, output_format="markdown")

            output = buf.getvalue()
            self.assertIn("# AgentGuard Incident Report", output)
            self.assertIn("guard.loop_detected", output)

    def test_incident_command_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 1, "error": None}) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._incident(path, output_format="json")

            output = json.loads(buf.getvalue())
            self.assertEqual(output["status"], "ok")


if __name__ == "__main__":
    unittest.main()
