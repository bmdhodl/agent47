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


class TestIncidentRendering(unittest.TestCase):
    def test_markdown_report_contains_upgrade_path(self):
        report = render_incident_report(
            [
                {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 500, "cost_usd": 1.2, "error": None},
                {"name": "guard.loop_detected", "kind": "event", "phase": "emit", "data": {"message": "loop"}, "error": None},
            ],
            output_format="markdown",
        )
        self.assertIn("# AgentGuard Incident Report", report)
        self.assertIn("Estimated savings: $1.2000", report)
        self.assertIn("HttpSink", report)

    def test_html_report_contains_title(self):
        report = render_incident_report(
            [{"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 10, "error": None}],
            output_format="html",
        )
        self.assertIn("<title>AgentGuard Incident Report</title>", report)

    def test_json_report_is_parseable(self):
        report = render_incident_report(
            [{"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 10, "error": None}],
            output_format="json",
        )
        data = json.loads(report)
        self.assertEqual(data["status"], "ok")


if __name__ == "__main__":
    unittest.main()
