"""OpenTelemetry TraceSink — bridges AgentGuard events to OTel spans.

Converts AgentGuard span start/end events into OpenTelemetry spans,
preserving trace_id, span_id, parent_id relationships.

Usage::

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    from agentguard.sinks.otel import OtelTraceSink
    from agentguard import Tracer

    sink = OtelTraceSink(provider)
    tracer = Tracer(sink=sink, service="my-agent")

    with tracer.trace("agent.run") as ctx:
        ctx.event("step", data={"thought": "search docs"})

Requires ``opentelemetry-api`` and ``opentelemetry-sdk`` (optional deps).
Core SDK remains zero-dep.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from agentguard.tracing import TraceSink

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.trace import StatusCode, SpanKind
    from opentelemetry.context import Context

    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False


class OtelTraceSink(TraceSink):
    """Sink that maps AgentGuard events to OpenTelemetry spans.

    Span lifecycle:
    - ``kind=span, phase=start`` → starts an OTel span (stored by span_id)
    - ``kind=span, phase=end`` → ends the OTel span, sets status/attributes
    - ``kind=event, phase=emit`` → adds an OTel event to the current span

    Args:
        tracer_provider: An OpenTelemetry TracerProvider instance.
        tracer_name: Name for the OTel tracer. Defaults to ``"agentguard"``.

    Raises:
        ImportError: If ``opentelemetry-api`` is not installed.
    """

    def __init__(
        self,
        tracer_provider: Any,
        tracer_name: str = "agentguard",
    ) -> None:
        if not _HAS_OTEL:
            raise ImportError(
                "opentelemetry-api is required for OtelTraceSink. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk"
            )
        self._otel_tracer = tracer_provider.get_tracer(tracer_name)
        self._spans: Dict[str, Any] = {}  # span_id -> OTel Span

    def emit(self, event: Dict[str, Any]) -> None:
        """Process an AgentGuard event and map to OTel.

        Args:
            event: AgentGuard event dict with kind, phase, trace_id, span_id, etc.
        """
        kind = event.get("kind")
        phase = event.get("phase")
        span_id = event.get("span_id")
        name = event.get("name", "unknown")

        if kind == "span" and phase == "start":
            self._start_span(event, name, span_id)
        elif kind == "span" and phase == "end":
            self._end_span(event, span_id)
        elif kind == "event":
            self._add_event(event, name, span_id)

    def _start_span(
        self, event: Dict[str, Any], name: str, span_id: Optional[str]
    ) -> None:
        """Start a new OTel span."""
        parent_id = event.get("parent_id")

        # Start span — OTel manages context internally
        span = self._otel_tracer.start_span(
            name=name,
            kind=SpanKind.INTERNAL,
        )

        # Set initial attributes
        attrs = {
            "agentguard.trace_id": event.get("trace_id", ""),
            "agentguard.span_id": span_id or "",
            "agentguard.service": event.get("service", ""),
        }
        if parent_id:
            attrs["agentguard.parent_id"] = parent_id
        if event.get("metadata"):
            for k, v in event["metadata"].items():
                attrs[f"agentguard.metadata.{k}"] = str(v)
        if event.get("data"):
            for k, v in event["data"].items():
                attrs[f"agentguard.data.{k}"] = str(v)[:256]

        for k, v in attrs.items():
            span.set_attribute(k, v)

        if span_id:
            self._spans[span_id] = span

    def _end_span(self, event: Dict[str, Any], span_id: Optional[str]) -> None:
        """End an existing OTel span."""
        if not span_id or span_id not in self._spans:
            return

        span = self._spans.pop(span_id)

        # Set duration and cost attributes
        duration_ms = event.get("duration_ms")
        if duration_ms is not None:
            span.set_attribute("agentguard.duration_ms", duration_ms)

        cost_usd = event.get("cost_usd")
        if cost_usd is not None:
            span.set_attribute("agentguard.cost_usd", cost_usd)

        # Set end data attributes
        if event.get("data"):
            for k, v in event["data"].items():
                span.set_attribute(f"agentguard.data.{k}", str(v)[:256])

        # Set error status
        error = event.get("error")
        if error:
            span.set_status(StatusCode.ERROR, str(error.get("message", "")))
            span.set_attribute("agentguard.error.type", error.get("type", ""))
            span.set_attribute("agentguard.error.message", str(error.get("message", ""))[:500])
        else:
            span.set_status(StatusCode.OK)

        span.end()

    def _add_event(
        self, event: Dict[str, Any], name: str, span_id: Optional[str]
    ) -> None:
        """Add an event to the parent span."""
        parent_id = event.get("parent_id") or span_id
        if not parent_id or parent_id not in self._spans:
            return

        span = self._spans[parent_id]
        attrs: Dict[str, Any] = {}
        if event.get("data"):
            for k, v in event["data"].items():
                attrs[k] = str(v)[:256]

        span.add_event(name, attributes=attrs)

    def shutdown(self) -> None:
        """End any orphaned spans (safety net)."""
        for span_id, span in list(self._spans.items()):
            try:
                span.set_status(StatusCode.ERROR, "orphaned span")
                span.end()
            except Exception:
                pass
        self._spans.clear()
