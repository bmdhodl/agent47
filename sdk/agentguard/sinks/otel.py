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

    sink = OtelTraceSink(provider, resource_attributes={"deployment.env": "prod"})
    tracer = Tracer(sink=sink, service="my-agent")

    with tracer.trace("agent.run") as ctx:
        ctx.event("step", data={"thought": "search docs"})

Custom resource attributes are stamped onto every span this sink emits, so
downstream collectors can filter on deployment/host/region without a hosted
control plane. Span links let one span point at sibling spans it consumed
(e.g. a fan-in step referencing the spans it merged); supply a ``links`` list
on the span-start event.

Requires ``opentelemetry-api`` and ``opentelemetry-sdk`` (optional deps).
Core SDK remains zero-dep.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from agentguard.tracing import TraceSink

try:
    from opentelemetry.trace import Link, SpanKind, StatusCode

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
        resource_attributes: Optional flat dict of attributes stamped onto
            every span this sink emits (e.g. ``{"deployment.env": "prod"}``).
            Values are coerced to strings. Defaults to no extra attributes.

    Raises:
        ImportError: If ``opentelemetry-api`` is not installed.
    """

    def __init__(
        self,
        tracer_provider: Any,
        tracer_name: str = "agentguard",
        resource_attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not _HAS_OTEL:
            raise ImportError(
                "opentelemetry-api is required for OtelTraceSink. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk"
            )
        self._otel_tracer = tracer_provider.get_tracer(tracer_name)
        self._lock = threading.Lock()
        self._spans: Dict[str, Any] = {}  # span_id -> OTel Span
        # Stamp resource-level attributes onto every span. Coerced to str so a
        # caller passing ints/bools cannot break OTel attribute validation.
        self._resource_attributes: Dict[str, str] = {
            f"agentguard.resource.{k}": str(v)
            for k, v in (resource_attributes or {}).items()
        }

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

    def _build_links(self, event: Dict[str, Any]) -> List[Any]:
        """Build OTel Link objects from an event's ``links`` field.

        Each link entry is a dict ``{"span_id": ..., "attributes": {...}}``
        referencing another AgentGuard span this sink already tracks. Links to
        unknown span_ids are skipped (the referenced span may have ended or
        never started). Returns an empty list when there are no resolvable
        links.
        """
        raw_links = event.get("links")
        if not raw_links:
            return []

        links: List[Any] = []
        for entry in raw_links:
            if not isinstance(entry, dict):
                continue
            ref_span_id = entry.get("span_id")
            if not ref_span_id:
                continue
            with self._lock:
                ref_span = self._spans.get(ref_span_id)
            if ref_span is None:
                continue
            link_attrs = {
                str(k): str(v)[:256]
                for k, v in (entry.get("attributes") or {}).items()
            }
            links.append(Link(ref_span.get_span_context(), attributes=link_attrs))
        return links

    def _start_span(
        self, event: Dict[str, Any], name: str, span_id: Optional[str]
    ) -> None:
        """Start a new OTel span, linking to parent if one exists."""
        parent_id = event.get("parent_id")

        # If there's a parent span we already track, set it as OTel context
        ctx = None
        if parent_id:
            with self._lock:
                parent_span = self._spans.get(parent_id)
            if parent_span and _HAS_OTEL:
                from opentelemetry.trace import set_span_in_context

                ctx = set_span_in_context(parent_span)

        links = self._build_links(event)

        span = self._otel_tracer.start_span(
            name=name,
            kind=SpanKind.INTERNAL,
            context=ctx,
            links=links,
        )

        # Set initial attributes
        attrs = {
            "agentguard.trace_id": event.get("trace_id", ""),
            "agentguard.span_id": span_id or "",
            "agentguard.service": event.get("service", ""),
        }
        # Resource-level attributes stamped on every span.
        attrs.update(self._resource_attributes)
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
            with self._lock:
                self._spans[span_id] = span

    def _end_span(self, event: Dict[str, Any], span_id: Optional[str]) -> None:
        """End an existing OTel span."""
        with self._lock:
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

        # Set error status — handle both dict and string error values
        error = event.get("error")
        if error:
            if isinstance(error, dict):
                msg = str(error.get("message", ""))
                err_type = error.get("type", "")
            else:
                msg = str(error)
                err_type = type(error).__name__
            span.set_status(StatusCode.ERROR, msg)
            span.set_attribute("agentguard.error.type", err_type)
            span.set_attribute("agentguard.error.message", msg[:500])
        else:
            span.set_status(StatusCode.OK)

        span.end()

    def _add_event(
        self, event: Dict[str, Any], name: str, span_id: Optional[str]
    ) -> None:
        """Add an event to the parent span."""
        parent_id = event.get("parent_id") or span_id
        with self._lock:
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
        with self._lock:
            spans = list(self._spans.items())
            self._spans.clear()
        for _span_id, span in spans:
            try:
                span.set_status(StatusCode.ERROR, "orphaned span")
                span.end()
            except Exception:
                pass
