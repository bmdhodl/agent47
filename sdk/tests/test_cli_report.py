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


if __name__ == "__main__":
    unittest.main()
