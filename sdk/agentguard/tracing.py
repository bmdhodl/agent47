"""Tracing primitives: Tracer, TraceContext, and sinks.

Usage::

    from agentguard import Tracer, JsonlFileSink, LoopGuard

    tracer = Tracer(
        sink=JsonlFileSink("traces.jsonl"),
        service="my-agent",
        guards=[LoopGuard(max_repeats=3)],
    )
    with tracer.trace("agent.run") as span:
        span.event("reasoning.step", data={"thought": "search docs"})
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agentguard.cost import CostTracker
import json
import threading
import time
import uuid


class TraceSink:
    """Base class for trace event sinks.

    Subclass and implement ``emit()`` to send events to your backend.
    """

    def emit(self, event: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class StdoutSink(TraceSink):
    """Sink that prints events to stdout as JSON.

    Usage::

        tracer = Tracer(sink=StdoutSink())
    """

    def emit(self, event: Dict[str, Any]) -> None:
        print(json.dumps(event, sort_keys=True))

    def __repr__(self) -> str:
        return "StdoutSink()"


class JsonlFileSink(TraceSink):
    """Sink that appends events as JSONL to a file.

    Thread-safe. Each event is written as a single JSON line.

    Usage::

        sink = JsonlFileSink("traces.jsonl")
        tracer = Tracer(sink=sink)

    Args:
        path: Path to the output JSONL file.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()

    def emit(self, event: Dict[str, Any]) -> None:
        """Append an event as a JSON line to the file."""
        line = json.dumps(event, sort_keys=True)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def __repr__(self) -> str:
        return f"JsonlFileSink({self._path!r})"


@dataclass
class TraceContext:
    """Context for a trace span. Used as a context manager.

    Provides methods to create child spans and emit events within a trace.

    Usage::

        with tracer.trace("agent.run") as ctx:
            ctx.event("reasoning.step", data={"step": 1})
            with ctx.span("tool.search") as child:
                child.event("tool.result", data={"result": "found"})
    """

    tracer: "Tracer"
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    data: Optional[Dict[str, Any]]
    _start_time: Optional[float] = None
    _cost_tracker: Optional[Any] = None

    @property
    def cost(self) -> "CostTracker":
        """Lazy-initialized CostTracker for this trace.

        Returns:
            A CostTracker instance that accumulates costs for this span.
        """
        if self._cost_tracker is None:
            from agentguard.cost import CostTracker

            self._cost_tracker = CostTracker()
        return self._cost_tracker

    def __enter__(self) -> "TraceContext":
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

    def __exit__(self, exc_type, exc, tb) -> None:
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
        )
        # Do not suppress exceptions
        return False

    def span(self, name: str, data: Optional[Dict[str, Any]] = None) -> "TraceContext":
        """Create a child span within this trace.

        Args:
            name: Name of the child span.
            data: Optional data to attach to the span.

        Returns:
            A new TraceContext to use as a context manager.
        """
        return TraceContext(
            tracer=self.tracer,
            trace_id=self.trace_id,
            span_id=_new_id(),
            parent_id=self.span_id,
            name=name,
            data=data,
        )

    def event(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit a point-in-time event within this span.

        Args:
            name: Name of the event.
            data: Optional data to attach to the event.
        """
        self.tracer._emit(
            kind="event",
            phase="emit",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_id=self.parent_id,
            name=name,
            data=data,
        )


class Tracer:
    """Core tracer that manages spans and emits events to a sink.

    Usage::

        from agentguard import Tracer, JsonlFileSink

        tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
        with tracer.trace("agent.run") as span:
            span.event("step", data={"thought": "search"})

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

    @contextmanager
    def trace(self, name: str, data: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a new top-level trace span.

        Args:
            name: Name of the trace span.
            data: Optional data to attach to the span.

        Yields:
            A TraceContext for creating child spans and events.
        """
        ctx = TraceContext(
            tracer=self,
            trace_id=_new_id(),
            span_id=_new_id(),
            parent_id=None,
            name=name,
            data=data,
        )
        with ctx:
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
        """Internal: build and emit a trace event.

        Also runs any attached guards on event emission.
        """
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
                # LoopGuard-style: pass name as tool_name
                try:
                    guard.check(name, data)
                except TypeError:
                    # Guard.check() doesn't accept these args (e.g. TimeoutGuard)
                    try:
                        guard.check()
                    except TypeError:
                        pass

    def __repr__(self) -> str:
        return f"Tracer(service={self._service!r}, sink={self._sink!r})"


def _new_id() -> str:
    return uuid.uuid4().hex
