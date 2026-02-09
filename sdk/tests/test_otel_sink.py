"""Tests for OTel TraceSink.

Since opentelemetry-sdk is an optional dependency, these tests mock the OTel
interfaces to verify our mapping logic without requiring the actual SDK.
"""
from __future__ import annotations

import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, call
import sys
import types


# Create mock OTel modules so we can test without opentelemetry installed
_mock_trace = types.ModuleType("opentelemetry.trace")
_mock_trace.StatusCode = type("StatusCode", (), {"OK": 1, "ERROR": 2})()
_mock_trace.SpanKind = type("SpanKind", (), {"INTERNAL": 1})()

_mock_context = types.ModuleType("opentelemetry.context")
_mock_context.Context = type("Context", (), {})

_mock_otel = types.ModuleType("opentelemetry")
_mock_otel.trace = _mock_trace


class FakeSpan:
    """Mock OTel Span that records calls."""

    def __init__(self, name: str):
        self.name = name
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status_code: Any = None
        self.status_message: str = ""
        self.ended = False

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({"name": name, "attributes": attributes or {}})

    def set_status(self, code: Any, message: str = "") -> None:
        self.status_code = code
        self.status_message = message

    def end(self) -> None:
        self.ended = True


class FakeTracer:
    """Mock OTel Tracer."""

    def __init__(self):
        self.spans: List[FakeSpan] = []

    def start_span(self, name: str, kind: Any = None) -> FakeSpan:
        span = FakeSpan(name)
        self.spans.append(span)
        return span


class FakeTracerProvider:
    """Mock OTel TracerProvider."""

    def __init__(self):
        self._tracer = FakeTracer()

    def get_tracer(self, name: str) -> FakeTracer:
        return self._tracer


class TestOtelTraceSink(unittest.TestCase):
    def setUp(self) -> None:
        # Patch OTel imports
        self._patches = {
            "opentelemetry": _mock_otel,
            "opentelemetry.trace": _mock_trace,
            "opentelemetry.context": _mock_context,
        }
        for name, mod in self._patches.items():
            sys.modules[name] = mod

        # Force reimport to pick up mocks
        if "agentguard.sinks.otel" in sys.modules:
            del sys.modules["agentguard.sinks.otel"]

        from agentguard.sinks.otel import OtelTraceSink
        self.OtelTraceSink = OtelTraceSink
        self.provider = FakeTracerProvider()

    def tearDown(self) -> None:
        for name in self._patches:
            sys.modules.pop(name, None)
        sys.modules.pop("agentguard.sinks.otel", None)

    def test_span_lifecycle(self):
        """Start + end events create and close an OTel span."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span",
            "phase": "start",
            "trace_id": "abc123",
            "span_id": "span1",
            "name": "agent.run",
            "service": "test",
            "ts": 1000.0,
            "data": {"user": "test"},
        })

        sink.emit({
            "kind": "span",
            "phase": "end",
            "trace_id": "abc123",
            "span_id": "span1",
            "name": "agent.run",
            "ts": 1001.0,
            "duration_ms": 1000.0,
        })

        tracer = self.provider._tracer
        self.assertEqual(len(tracer.spans), 1)
        span = tracer.spans[0]
        self.assertEqual(span.name, "agent.run")
        self.assertTrue(span.ended)
        self.assertEqual(span.attributes["agentguard.duration_ms"], 1000.0)

    def test_span_with_error(self):
        """Span end with error sets ERROR status."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "failing",
            "ts": 100.0, "service": "test",
        })
        sink.emit({
            "kind": "span", "phase": "end",
            "trace_id": "t1", "span_id": "s1", "name": "failing",
            "ts": 101.0, "duration_ms": 1000.0,
            "error": {"type": "ValueError", "message": "bad input"},
        })

        span = self.provider._tracer.spans[0]
        self.assertTrue(span.ended)
        # StatusCode.ERROR = 2
        self.assertEqual(span.status_code, 2)
        self.assertEqual(span.attributes["agentguard.error.type"], "ValueError")

    def test_point_event(self):
        """Point events are added to the parent span."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "parent",
            "ts": 100.0, "service": "test",
        })
        sink.emit({
            "kind": "event", "phase": "emit",
            "trace_id": "t1", "span_id": "evt1", "parent_id": "s1",
            "name": "reasoning.step",
            "ts": 100.5,
            "data": {"thought": "search docs"},
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(len(span.events), 1)
        self.assertEqual(span.events[0]["name"], "reasoning.step")
        self.assertEqual(span.events[0]["attributes"]["thought"], "search docs")

    def test_cost_attribute(self):
        """Cost USD is set as span attribute on end."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "llm",
            "ts": 100.0, "service": "test",
        })
        sink.emit({
            "kind": "span", "phase": "end",
            "trace_id": "t1", "span_id": "s1", "name": "llm",
            "ts": 100.5, "duration_ms": 500.0, "cost_usd": 0.03,
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(span.attributes["agentguard.cost_usd"], 0.03)

    def test_metadata_as_attributes(self):
        """Metadata from events becomes span attributes."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
            "metadata": {"env": "prod", "version": "0.6.0"},
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(span.attributes["agentguard.metadata.env"], "prod")
        self.assertEqual(span.attributes["agentguard.metadata.version"], "0.6.0")

    def test_parent_id_attribute(self):
        """Parent span ID is set as attribute."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s2", "parent_id": "s1",
            "name": "child", "ts": 100.0, "service": "test",
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(span.attributes["agentguard.parent_id"], "s1")

    def test_shutdown_ends_orphans(self):
        """Shutdown ends any unclosed spans."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "orphan",
            "name": "leaked", "ts": 100.0, "service": "test",
        })

        sink.shutdown()

        span = self.provider._tracer.spans[0]
        self.assertTrue(span.ended)
        self.assertEqual(span.status_code, 2)  # ERROR

    def test_end_without_start_ignored(self):
        """End event for unknown span_id is silently ignored."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "end",
            "trace_id": "t1", "span_id": "unknown",
            "name": "ghost", "ts": 100.0,
        })

        self.assertEqual(len(self.provider._tracer.spans), 0)

    def test_custom_tracer_name(self):
        """Custom tracer name is passed to provider."""
        provider = FakeTracerProvider()
        sink = self.OtelTraceSink(provider, tracer_name="custom-agent")
        # Tracer was requested — just verify no error
        self.assertIsNotNone(sink)


if __name__ == "__main__":
    unittest.main()
