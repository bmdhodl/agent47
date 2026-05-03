import json
import os
import tempfile
import unittest

from agentguard.reporting import render_incident_report, summarize_incident


def _write_trace(events):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return path


class TestIncidentSummary(unittest.TestCase):
    def test_budget_exceeded_summary(self):
        path = _write_trace(
            [
                {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 250, "cost_usd": 2.5, "error": None},
                {
                    "name": "guard.budget_exceeded",
                    "kind": "event",
                    "phase": "emit",
                    "data": {"message": "Cost budget exceeded: $2.5000 > $2.0000"},
                    "error": None,
                },
            ]
        )
        try:
            incident = summarize_incident(path)
            self.assertEqual(incident["severity"], "critical")
            self.assertEqual(incident["primary_cause"], "budget_exceeded")
            self.assertEqual(incident["guard_event_count"], 1)
            self.assertAlmostEqual(incident["estimated_savings_usd"], 2.5)
            self.assertAlmostEqual(incident["exact_savings_usd"], 0.0)
            self.assertEqual(incident["savings"]["estimated_tokens_saved"], 0)
            self.assertAlmostEqual(incident["savings"]["estimated_usd_saved"], 2.5)
            self.assertEqual(incident["savings"]["reasons"][0]["kind"], "budget_overrun_stopped")
        finally:
            os.unlink(path)

    def test_warning_only_summary(self):
        incident = summarize_incident(
            [
                {"name": "guard.budget_warning", "kind": "event", "phase": "emit", "data": {}, "error": None},
            ]
        )
        self.assertEqual(incident["severity"], "warning")
        self.assertEqual(incident["primary_cause"], "budget_warning")
        self.assertEqual(incident["estimated_savings_usd"], 0.0)

    def test_non_dict_error_marks_incident(self):
        incident = summarize_incident(
            [
                {
                    "name": "agent.run",
                    "kind": "span",
                    "phase": "end",
                    "duration_ms": 10,
                    "error": "boom",
                },
            ]
        )
        self.assertEqual(incident["severity"], "critical")
        self.assertEqual(incident["status"], "incident")
        self.assertEqual(incident["primary_cause"], "error")

    def test_error_incident_keeps_legacy_estimate_without_ledger_overwrite(self):
        incident = summarize_incident(
            [
                {
                    "name": "agent.run",
                    "kind": "span",
                    "phase": "end",
                    "duration_ms": 10,
                    "cost_usd": 1.0,
                    "error": {"type": "RuntimeError", "message": "boom"},
                },
            ]
        )
        self.assertEqual(incident["primary_cause"], "error")
        self.assertAlmostEqual(incident["estimated_savings_usd"], 0.5)
        self.assertAlmostEqual(incident["savings"]["estimated_usd_saved"], 0.0)

    def test_retry_limit_exceeded_sets_primary_cause(self):
        incident = summarize_incident(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
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
                    "name": "guard.retry_limit_exceeded",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "retry limit exceeded"},
                    "error": None,
                },
            ]
        )
        self.assertEqual(incident["severity"], "critical")
        self.assertEqual(incident["primary_cause"], "retry_limit_exceeded")
        self.assertIn("exponential backoff", incident["recommendations"][0])
        self.assertTrue(
            any(
                "Keep one-off investigations local" in recommendation
                for recommendation in incident["recommendations"]
            )
        )


class TestIncidentRendering(unittest.TestCase):
    def test_markdown_report_contains_upgrade_path(self):
        report = render_incident_report(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
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
                    "name": "guard.loop_detected",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "loop"},
                    "error": None,
                },
            ],
            output_format="markdown",
        )
        self.assertIn("# AgentGuard Incident Report", report)
        self.assertIn("## Savings Ledger", report)
        self.assertIn("Estimated savings: $0.0075", report)
        self.assertIn("`loop_prevented` (estimated): 1500 tokens / $0.0075", report)
        self.assertIn("Keep this report local if it is a one-off investigation.", report)
        self.assertIn("retained history, alerts, spend trends", report)
        self.assertIn("HttpSink", report)

    def test_html_report_contains_title(self):
        report = render_incident_report(
            [{"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 10, "error": None}],
            output_format="html",
        )
        self.assertIn("<title>AgentGuard Incident Report</title>", report)
        self.assertIn("Keep this report local if it is a one-off investigation.", report)

    def test_json_report_is_parseable(self):
        report = render_incident_report(
            [{"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 10, "error": None}],
            output_format="json",
        )
        data = json.loads(report)
        self.assertEqual(data["status"], "ok")
        self.assertIn("savings", data)
        self.assertEqual(data["savings"]["exact_tokens_saved"], 0)


if __name__ == "__main__":
    unittest.main()
