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
_mock_trace.set_span_in_context = lambda span, context=None: {"parent_span": span}


class _MockLink:
    """Mock OTel Link — records the linked span context and attributes."""

    def __init__(self, context, attributes=None):
        self.context = context
        self.attributes = attributes or {}


_mock_trace.Link = _MockLink

_mock_context = types.ModuleType("opentelemetry.context")
_mock_context.Context = type("Context", (), {})

_mock_otel = types.ModuleType("opentelemetry")
_mock_otel.trace = _mock_trace
_mock_otel.context = _mock_context


class FakeSpan:
    """Mock OTel Span that records calls."""

    _ctx_counter = 0

    def __init__(self, name: str):
        self.name = name
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status_code: Any = None
        self.status_message: str = ""
        self.ended = False
        self.parent_context: Any = None
        self.links: List[Any] = []
        FakeSpan._ctx_counter += 1
        # Stable unique stand-in for an OTel SpanContext.
        self._span_context = ("span-context", name, FakeSpan._ctx_counter)

    def get_span_context(self) -> Any:
        return self._span_context

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

    def start_span(
        self,
        name: str,
        kind: Any = None,
        context: Any = None,
        links: Any = None,
    ) -> FakeSpan:
        span = FakeSpan(name)
        span.parent_context = context
        span.links = list(links or [])
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

    def test_parent_child_linking(self):
        """Child span receives parent context for proper OTel linking."""
        sink = self.OtelTraceSink(self.provider)

        # Start parent
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "parent",
            "name": "agent.run", "ts": 100.0, "service": "test",
        })
        # Start child with parent_id
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "child", "parent_id": "parent",
            "name": "tool.search", "ts": 100.1, "service": "test",
        })

        tracer = self.provider._tracer
        self.assertEqual(len(tracer.spans), 2)
        parent_span = tracer.spans[0]
        child_span = tracer.spans[1]

        # Child should have received a context containing the parent span
        self.assertIsNotNone(child_span.parent_context)
        self.assertEqual(child_span.parent_context["parent_span"], parent_span)

        # Parent should have no parent context
        self.assertIsNone(parent_span.parent_context)

    def test_string_error_handling(self):
        """Error field as string (not dict) doesn't crash."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
        })
        sink.emit({
            "kind": "span", "phase": "end",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 101.0, "duration_ms": 1000.0,
            "error": "something broke",
        })

        span = self.provider._tracer.spans[0]
        self.assertTrue(span.ended)
        self.assertEqual(span.status_code, 2)  # ERROR
        self.assertEqual(span.attributes["agentguard.error.message"], "something broke")
        self.assertEqual(span.attributes["agentguard.error.type"], "str")


    def test_resource_attributes_stamped_on_every_span(self):
        """Custom resource attributes appear on every emitted span."""
        sink = self.OtelTraceSink(
            self.provider,
            resource_attributes={"deployment.env": "prod", "host": "node-1"},
        )

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "first",
            "ts": 100.0, "service": "test",
        })
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s2", "name": "second",
            "ts": 101.0, "service": "test",
        })

        for span in self.provider._tracer.spans:
            self.assertEqual(
                span.attributes["agentguard.resource.deployment.env"], "prod"
            )
            self.assertEqual(
                span.attributes["agentguard.resource.host"], "node-1"
            )

    def test_resource_attributes_coerced_to_string(self):
        """Non-string resource attribute values are coerced to strings."""
        sink = self.OtelTraceSink(
            self.provider,
            resource_attributes={"replica": 3, "canary": True},
        )

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(span.attributes["agentguard.resource.replica"], "3")
        self.assertEqual(span.attributes["agentguard.resource.canary"], "True")

    def test_no_resource_attributes_by_default(self):
        """Without resource_attributes, no agentguard.resource.* keys appear."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
        })

        span = self.provider._tracer.spans[0]
        resource_keys = [
            k for k in span.attributes if k.startswith("agentguard.resource.")
        ]
        self.assertEqual(resource_keys, [])

    def test_span_link_to_tracked_span(self):
        """A span-start event with links produces an OTel Link to the target."""
        sink = self.OtelTraceSink(self.provider)

        # Start the span that will be linked to.
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "source", "name": "producer",
            "ts": 100.0, "service": "test",
        })
        # Start a span that links back to the source span.
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "consumer", "name": "fan-in",
            "ts": 101.0, "service": "test",
            "links": [
                {"span_id": "source", "attributes": {"relation": "merged"}}
            ],
        })

        consumer_span = self.provider._tracer.spans[1]
        source_span = self.provider._tracer.spans[0]
        self.assertEqual(len(consumer_span.links), 1)
        link = consumer_span.links[0]
        self.assertEqual(link.context, source_span.get_span_context())
        self.assertEqual(link.attributes["relation"], "merged")

    def test_span_link_to_unknown_span_skipped(self):
        """Links referencing untracked span_ids are silently skipped."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
            "links": [{"span_id": "does-not-exist"}],
        })

        span = self.provider._tracer.spans[0]
        self.assertEqual(span.links, [])

    def test_multiple_span_links(self):
        """A span can link to multiple tracked spans at once."""
        sink = self.OtelTraceSink(self.provider)

        for sid in ("a", "b"):
            sink.emit({
                "kind": "span", "phase": "start",
                "trace_id": "t1", "span_id": sid, "name": sid,
                "ts": 100.0, "service": "test",
            })
        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "joiner", "name": "join",
            "ts": 101.0, "service": "test",
            "links": [{"span_id": "a"}, {"span_id": "b"}],
        })

        joiner = self.provider._tracer.spans[-1]
        self.assertEqual(len(joiner.links), 2)

    def test_no_links_by_default(self):
        """A span-start event without links produces a span with no links."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
        })

        self.assertEqual(self.provider._tracer.spans[0].links, [])

    def test_malformed_link_entries_skipped(self):
        """Non-dict link entries and entries without span_id are skipped."""
        sink = self.OtelTraceSink(self.provider)

        sink.emit({
            "kind": "span", "phase": "start",
            "trace_id": "t1", "span_id": "s1", "name": "op",
            "ts": 100.0, "service": "test",
            "links": ["not-a-dict", {"attributes": {"x": "y"}}, None],
        })

        self.assertEqual(self.provider._tracer.spans[0].links, [])


if __name__ == "__main__":
    unittest.main()
