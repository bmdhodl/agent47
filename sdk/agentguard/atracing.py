"""Async tracing primitives: AsyncTracer and AsyncTraceContext.

Reuses sync sinks — _emit() stays synchronous (HttpSink already uses
a background thread, so there's no need for async I/O).

Usage::

    from agentguard import AsyncTracer, JsonlFileSink

    tracer = AsyncTracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
    async with tracer.trace("agent.run") as span:
        span.event("reasoning.step", data={"thought": "search docs"})
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional

if TYPE_CHECKING:
    from agentguard.cost import CostTracker

import time
import uuid

from agentguard.tracing import StdoutSink, TraceSink


@dataclass
class AsyncTraceContext:
    """Async context for a trace span.

    Usage::

        async with tracer.trace("agent.run") as ctx:
            ctx.event("step", data={"thought": "search"})
            async with ctx.span("tool.search") as child:
                child.event("tool.result", data={"result": "found"})
    """

    tracer: "AsyncTracer"
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    data: Optional[Dict[str, Any]]
    _start_time: Optional[float] = None
    _cost_tracker: Optional[Any] = None

    @property
    def cost(self) -> "CostTracker":
        """Lazy-initialized CostTracker for this trace."""
        if self._cost_tracker is None:
            from agentguard.cost import CostTracker

            self._cost_tracker = CostTracker()
        return self._cost_tracker

    async def __aenter__(self) -> "AsyncTraceContext":
        self._start_time = time.perf_counter()
        self.tracer._emit(
            kind="span",
            phase="start",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_id=self.parent_id,
            name=self.name,
            data=self.data,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        end = time.perf_counter()
        duration_ms = None
        if self._start_time is not None:
            duration_ms = (end - self._start_time) * 1000.0
        error = None
        if exc is not None:
            error = {
                "type": getattr(exc_type, "__name__", "Exception"),
                "message": str(exc),
            }
        # Include accumulated cost from CostTracker if any
        cost_usd = None
        if self._cost_tracker is not None and self._cost_tracker.total > 0:
            cost_usd = self._cost_tracker.total
        self.tracer._emit(
            kind="span",
            phase="end",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_id=self.parent_id,
            name=self.name,
            data=self.data,
            duration_ms=duration_ms,
            error=error,
            cost_usd=cost_usd,
        )

    @asynccontextmanager
    async def span(self, name: str, data: Optional[Dict[str, Any]] = None) -> AsyncIterator["AsyncTraceContext"]:
        """Create a child span within this trace.

        Args:
            name: Name of the child span.
            data: Optional data to attach.

        Yields:
            A new AsyncTraceContext.
        """
        ctx = AsyncTraceContext(
            tracer=self.tracer,
            trace_id=self.trace_id,
            span_id=_new_id(),
            parent_id=self.span_id,
            name=name,
            data=data,
        )
        async with ctx:
            yield ctx

    def event(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Emit a point-in-time event within this span.

        Note: event() is synchronous — no I/O is performed directly.

        Args:
            name: Name of the event.
            data: Optional data to attach to the event.
            cost_usd: Optional cost in USD for this event.
        """
        self.tracer._emit(
            kind="event",
            phase="emit",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_id=self.parent_id,
            name=name,
            data=data,
            cost_usd=cost_usd,
        )


class AsyncTracer:
    """Async tracer that manages spans and emits events to a sync sink.

    The sink's emit() is called synchronously — HttpSink already handles
    I/O in a background thread, so no async sink is needed.

    Usage::

        tracer = AsyncTracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
        async with tracer.trace("agent.run") as span:
            span.event("reasoning.step", data={"thought": "search docs"})

    Args:
        sink: Where to send trace events. Defaults to StdoutSink.
        service: Name of the service being traced.
        guards: Optional list of guards to auto-check on each event.
    """

    def __init__(
        self,
        sink: Optional[TraceSink] = None,
        service: str = "app",
        guards: Optional[List[Any]] = None,
    ) -> None:
        self._sink = sink or StdoutSink()
        self._service = service
        self._guards = guards or []

    @asynccontextmanager
    async def trace(self, name: str, data: Optional[Dict[str, Any]] = None) -> AsyncIterator[AsyncTraceContext]:
        """Start a new top-level async trace span.

        Args:
            name: Name of the trace span.
            data: Optional data to attach.

        Yields:
            An AsyncTraceContext for creating child spans and events.
        """
        ctx = AsyncTraceContext(
            tracer=self,
            trace_id=_new_id(),
            span_id=_new_id(),
            parent_id=None,
            name=name,
            data=data,
        )
        async with ctx:
            yield ctx

    def _emit(
        self,
        *,
        kind: str,
        phase: str,
        trace_id: str,
        span_id: str,
        parent_id: Optional[str],
        name: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Dict[str, Any]] = None,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Internal: build and emit a trace event (sync)."""
        event: Dict[str, Any] = {
            "service": self._service,
            "kind": kind,
            "phase": phase,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_id": parent_id,
            "name": name,
            "ts": time.time(),
            "duration_ms": duration_ms,
            "data": data or {},
            "error": error,
        }
        if cost_usd is not None:
            event["cost_usd"] = cost_usd
        self._sink.emit(event)

        # Auto-check guards
        for guard in self._guards:
            if hasattr(guard, "check") and kind == "event":
                try:
                    guard.check(name, data)
                except TypeError:
                    try:
                        guard.check()
                    except TypeError:
                        pass

    def __repr__(self) -> str:
        return f"AsyncTracer(service={self._service!r}, sink={self._sink!r})"


def _new_id() -> str:
    return uuid.uuid4().hex
