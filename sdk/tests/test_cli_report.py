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
            self.assertIn("Savings ledger: exact 0 tokens / $0.0000, estimated 0 tokens / $0.0000", output)

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

    def test_incident_command_markdown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "kind": "event",
                    "trace_id": "t1",
                    "name": "llm.result",
                    "ts": 0,
                    "phase": "emit",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 500,
                            "total_tokens": 1500,
                        },
                    },
                    "error": None,
                },
                {
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
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
                cli._incident(path, output_format="markdown")

            output = buf.getvalue()
            self.assertIn("# AgentGuard Incident Report", output)
            self.assertIn("guard.loop_detected", output)
            self.assertIn("## Savings Ledger", output)
            self.assertIn("Estimated tokens saved: 1500", output)

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
            self.assertIn("savings", output)

    def test_report_empty_json_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "empty.jsonl")
            open(path, "w", encoding="utf-8").close()

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._report(path, as_json=True)

            output = json.loads(buf.getvalue())
            self.assertEqual(output["error"], "No events found")

    def test_report_json_includes_savings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "name": "llm.result",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 500,
                            "total_tokens": 1500,
                        },
                    },
                    "error": None,
                },
                {
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "name": "guard.retry_limit_exceeded",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {"message": "retry limit"},
                    "error": None,
                },
            ]
            with open(path, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._report(path, as_json=True)

            output = json.loads(buf.getvalue())
            self.assertEqual(output["savings"]["estimated_tokens_saved"], 1500)
            self.assertAlmostEqual(output["savings"]["estimated_usd_saved"], 0.0075, places=4)

    def test_decisions_command_outputs_human_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            events = [
                {
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "name": "decision.proposed",
                    "ts": 0,
                    "duration_ms": None,
                    "data": {
                        "decision_id": "dec_1",
                        "workflow_id": "wf_1",
                        "trace_id": "t1",
                        "object_type": "deployment",
                        "object_id": "deploy_1",
                        "actor_type": "agent",
                        "actor_id": "planner",
                        "event_type": "decision.proposed",
                        "proposal": {"action": "deploy"},
                        "final": {"action": "deploy"},
                        "diff": "",
                        "reason": None,
                        "comment": None,
                        "timestamp": "2026-04-07T00:00:00Z",
                        "binding_state": None,
                        "outcome": "proposed",
                    },
                    "error": None,
                }
            ]
            with open(path, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._decisions(path)

            output = buf.getvalue()
            self.assertIn("decision events: 1", output)
            self.assertIn("decision.proposed", output)
            self.assertIn("workflow=wf_1", output)

    def test_decisions_command_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "traces.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "kind": "event",
                            "phase": "emit",
                            "trace_id": "t1",
                            "name": "decision.bound",
                            "ts": 0,
                            "duration_ms": None,
                            "data": {
                                "decision_id": "dec_1",
                                "workflow_id": "wf_1",
                                "trace_id": "t1",
                                "object_type": "deployment",
                                "object_id": "deploy_1",
                                "actor_type": "system",
                                "actor_id": "deploy-api",
                                "event_type": "decision.bound",
                                "proposal": {"action": "deploy"},
                                "final": {"action": "deploy"},
                                "diff": "",
                                "reason": None,
                                "comment": None,
                                "timestamp": "2026-04-07T00:00:00Z",
                                "binding_state": "applied",
                                "outcome": "success",
                            },
                            "error": None,
                        }
                    )
                    + "\n"
                )

            buf = io.StringIO()
            with redirect_stdout(buf):
                cli._decisions(path, as_json=True)

            output = json.loads(buf.getvalue())
            self.assertEqual(output["count"], 1)
            self.assertEqual(output["decisions"][0]["event_type"], "decision.bound")


if __name__ == "__main__":
    unittest.main()
