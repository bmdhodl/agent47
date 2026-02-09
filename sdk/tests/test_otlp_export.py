"""Tests for OTLP JSON export."""
from __future__ import annotations

import json
import os
import tempfile
import time
import unittest

from agentguard.export import export_otlp, events_to_otlp, load_trace


def _make_trace_events(trace_id="t1", service="test"):
    """Build a minimal set of AgentGuard events (1 span + 1 child + 1 event)."""
    ts = 1700000000.0
    return [
        {
            "service": service,
            "kind": "span",
            "phase": "start",
            "trace_id": trace_id,
            "span_id": "span1",
            "parent_id": None,
            "name": "agent.run",
            "ts": ts,
            "data": {"user": "test"},
        },
        {
            "service": service,
            "kind": "span",
            "phase": "start",
            "trace_id": trace_id,
            "span_id": "span2",
            "parent_id": "span1",
            "name": "tool.search",
            "ts": ts + 0.1,
            "data": {"query": "AI agents"},
        },
        {
            "service": service,
            "kind": "event",
            "phase": "emit",
            "trace_id": trace_id,
            "span_id": "evt1",
            "parent_id": "span2",
            "name": "tool.result",
            "ts": ts + 0.3,
            "data": {"output": "Found 10 results"},
        },
        {
            "service": service,
            "kind": "span",
            "phase": "end",
            "trace_id": trace_id,
            "span_id": "span2",
            "parent_id": "span1",
            "name": "tool.search",
            "ts": ts + 0.5,
            "duration_ms": 400.0,
            "cost_usd": 0.01,
        },
        {
            "service": service,
            "kind": "span",
            "phase": "end",
            "trace_id": trace_id,
            "span_id": "span1",
            "name": "agent.run",
            "ts": ts + 1.0,
            "duration_ms": 1000.0,
            "cost_usd": 0.05,
        },
    ]


class TestEventsToOtlp(unittest.TestCase):
    def test_basic_structure(self):
        """Output has correct top-level OTLP structure."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        self.assertIn("resourceSpans", otlp)
        self.assertEqual(len(otlp["resourceSpans"]), 1)

        rs = otlp["resourceSpans"][0]
        self.assertIn("resource", rs)
        self.assertIn("scopeSpans", rs)

        # Check service name attribute
        attrs = rs["resource"]["attributes"]
        svc_attr = [a for a in attrs if a["key"] == "service.name"]
        self.assertEqual(len(svc_attr), 1)
        self.assertEqual(svc_attr[0]["value"]["stringValue"], "test")

    def test_span_count(self):
        """Correct number of spans produced."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        self.assertEqual(len(spans), 2)  # agent.run + tool.search

    def test_span_names(self):
        """Span names match AgentGuard event names."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        names = {s["name"] for s in spans}
        self.assertEqual(names, {"agent.run", "tool.search"})

    def test_parent_span_id(self):
        """Child span has parentSpanId set."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        child = [s for s in spans if s["name"] == "tool.search"][0]
        self.assertIn("parentSpanId", child)

    def test_root_span_no_parent(self):
        """Root span has no parentSpanId."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        root = [s for s in spans if s["name"] == "agent.run"][0]
        self.assertNotIn("parentSpanId", root)

    def test_timestamps_are_nanoseconds(self):
        """Start/end times are in nanosecond strings."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        for span in spans:
            start = int(span["startTimeUnixNano"])
            end = int(span["endTimeUnixNano"])
            self.assertGreater(start, 0)
            self.assertGreaterEqual(end, start)

    def test_cost_attribute(self):
        """Cost USD is included in span attributes."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        child = [s for s in spans if s["name"] == "tool.search"][0]
        cost_attrs = [a for a in child["attributes"] if a["key"] == "cost_usd"]
        self.assertEqual(len(cost_attrs), 1)
        self.assertEqual(cost_attrs[0]["value"]["doubleValue"], 0.01)

    def test_events_attached_to_spans(self):
        """Point events appear as OTel events on the parent span."""
        events = _make_trace_events()
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        child = [s for s in spans if s["name"] == "tool.search"][0]
        self.assertEqual(len(child["events"]), 1)
        self.assertEqual(child["events"][0]["name"], "tool.result")

    def test_error_status(self):
        """Span with error gets STATUS_CODE_ERROR."""
        events = [
            {
                "service": "test", "kind": "span", "phase": "start",
                "trace_id": "t1", "span_id": "s1", "name": "failing",
                "ts": 100.0,
            },
            {
                "service": "test", "kind": "span", "phase": "end",
                "trace_id": "t1", "span_id": "s1", "name": "failing",
                "ts": 101.0, "duration_ms": 1000.0,
                "error": {"type": "ValueError", "message": "bad"},
            },
        ]
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        self.assertEqual(spans[0]["status"]["code"], 2)
        self.assertEqual(spans[0]["status"]["message"], "bad")

    def test_ok_status(self):
        """Span without error gets STATUS_CODE_OK."""
        events = [
            {
                "service": "test", "kind": "span", "phase": "start",
                "trace_id": "t1", "span_id": "s1", "name": "ok",
                "ts": 100.0,
            },
            {
                "service": "test", "kind": "span", "phase": "end",
                "trace_id": "t1", "span_id": "s1", "name": "ok",
                "ts": 101.0, "duration_ms": 1000.0,
            },
        ]
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        self.assertEqual(spans[0]["status"]["code"], 1)

    def test_custom_service_name(self):
        """Custom service name overrides event service."""
        events = _make_trace_events(service="from-event")
        otlp = events_to_otlp(events, service_name="override")

        attrs = otlp["resourceSpans"][0]["resource"]["attributes"]
        svc = [a for a in attrs if a["key"] == "service.name"][0]
        self.assertEqual(svc["value"]["stringValue"], "override")

    def test_attribute_types(self):
        """Different Python types map to correct OTLP value types."""
        events = [
            {
                "service": "test", "kind": "span", "phase": "start",
                "trace_id": "t1", "span_id": "s1", "name": "typed",
                "ts": 100.0,
                "data": {"count": 42, "rate": 0.95, "enabled": True, "name": "test"},
            },
            {
                "service": "test", "kind": "span", "phase": "end",
                "trace_id": "t1", "span_id": "s1", "name": "typed",
                "ts": 101.0, "duration_ms": 1000.0,
            },
        ]
        otlp = events_to_otlp(events)

        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        attrs = {a["key"]: a["value"] for a in spans[0]["attributes"]}

        self.assertEqual(attrs["count"]["intValue"], "42")
        self.assertEqual(attrs["rate"]["doubleValue"], 0.95)
        self.assertEqual(attrs["enabled"]["boolValue"], True)
        self.assertEqual(attrs["name"]["stringValue"], "test")

    def test_empty_events(self):
        """Empty event list produces valid structure with no spans."""
        otlp = events_to_otlp([])
        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        self.assertEqual(len(spans), 0)


class TestExportOtlpFile(unittest.TestCase):
    def test_file_export(self):
        """export_otlp writes valid OTLP JSON to file."""
        events = _make_trace_events()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as inp:
            for e in events:
                inp.write(json.dumps(e) + "\n")
            inp_path = inp.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as out:
            out_path = out.name

        try:
            count = export_otlp(inp_path, out_path)
            self.assertEqual(count, 2)  # 2 spans

            with open(out_path, "r") as f:
                data = json.load(f)

            self.assertIn("resourceSpans", data)
            spans = data["resourceSpans"][0]["scopeSpans"][0]["spans"]
            self.assertEqual(len(spans), 2)
        finally:
            os.unlink(inp_path)
            os.unlink(out_path)

    def test_file_export_with_service_name(self):
        """export_otlp uses custom service name."""
        events = _make_trace_events()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as inp:
            for e in events:
                inp.write(json.dumps(e) + "\n")
            inp_path = inp.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as out:
            out_path = out.name

        try:
            export_otlp(inp_path, out_path, service_name="my-service")

            with open(out_path, "r") as f:
                data = json.load(f)

            attrs = data["resourceSpans"][0]["resource"]["attributes"]
            svc = [a for a in attrs if a["key"] == "service.name"][0]
            self.assertEqual(svc["value"]["stringValue"], "my-service")
        finally:
            os.unlink(inp_path)
            os.unlink(out_path)


class TestHexPad(unittest.TestCase):
    def test_short_id(self):
        from agentguard.export import _hex_pad

        result = _hex_pad("abc", 16)
        self.assertEqual(len(result), 16)
        self.assertTrue(result.endswith("abc"))

    def test_uuid_with_dashes(self):
        from agentguard.export import _hex_pad

        result = _hex_pad("550e8400-e29b-41d4-a716-446655440000", 32)
        self.assertEqual(len(result), 32)
        self.assertNotIn("-", result)

    def test_already_correct_length(self):
        from agentguard.export import _hex_pad

        result = _hex_pad("abcdef1234567890", 16)
        self.assertEqual(result, "abcdef1234567890")


if __name__ == "__main__":
    unittest.main()
