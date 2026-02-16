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

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from agentguard.cost import CostTracker
import json
import random
import threading
import time
import uuid

logger = logging.getLogger("agentguard.tracing")

_MAX_NAME_LENGTH = 1000
_MAX_EVENT_DATA_BYTES = 65_536  # 64 KB


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
        with self._lock, open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def __repr__(self) -> str:
        return f"JsonlFileSink({self._path!r})"


def _truncate_name(name: str) -> str:
    """Truncate a name to _MAX_NAME_LENGTH chars, logging a warning if needed."""
    if len(name) <= _MAX_NAME_LENGTH:
        return name
    logger.warning(
        "Name truncated from %d to %d chars: %s...",
        len(name), _MAX_NAME_LENGTH, name[:50],
    )
    return name[:_MAX_NAME_LENGTH]


def _sanitize_data(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Validate event data size, replacing oversized payloads with a marker.

    Prevents OOM from malicious or buggy callers passing enormous data dicts.
    """
    if data is None:
        return None
    try:
        serialized = json.dumps(data, sort_keys=True)
    except (TypeError, ValueError):
        logger.warning("Event data is not JSON-serializable, replacing with marker")
        return {"_error": "not_serializable"}
    size = len(serialized.encode("utf-8"))
    if size > _MAX_EVENT_DATA_BYTES:
        logger.warning(
            "Event data truncated: %d bytes > %d limit",
            size, _MAX_EVENT_DATA_BYTES,
        )
        return {"_truncated": True, "_original_size_bytes": size}
    return data


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
    _sampled: bool = True

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
        if self._sampled:
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
        # Include accumulated cost from CostTracker if any
        cost_usd = None
        if self._cost_tracker is not None and self._cost_tracker.total > 0:
            cost_usd = self._cost_tracker.total
        if self._sampled:
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
            name=_truncate_name(name),
            data=data,
            _sampled=self._sampled,
        )

    def event(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Emit a point-in-time event within this span.

        Args:
            name: Name of the event.
            data: Optional data to attach to the event (max 64 KB serialized).
            cost_usd: Optional cost in USD for this event.
        """
        truncated_name = _truncate_name(name)
        safe_data = _sanitize_data(data)
        if self._sampled:
            self.tracer._emit(
                kind="event",
                phase="emit",
                trace_id=self.trace_id,
                span_id=self.span_id,
                parent_id=self.parent_id,
                name=truncated_name,
                data=safe_data,
                cost_usd=cost_usd,
            )
        else:
            # Guards must still fire even when trace is sampled out
            self.tracer._check_guards(truncated_name, safe_data)


class Tracer:
    """Core tracer that manages spans and emits events to a sink.

    Can be used as a context manager for clean shutdown::

        with Tracer(sink=HttpSink(...), service="my-agent") as tracer:
            with tracer.trace("agent.run") as span:
                span.event("step", data={"thought": "search"})
        # sink.shutdown() called automatically on exit

    Args:
        sink: Where to send trace events. Defaults to StdoutSink.
        service: Name of the service being traced.
        guards: Optional list of guards to auto-check on each event.
        metadata: Dict of metadata attached to every event (e.g. env, git SHA).
        sampling_rate: Float 0.0-1.0. Fraction of traces to emit. 1.0 = all, 0.0 = none.
    """

    def __init__(
        self,
        sink: Optional[TraceSink] = None,
        service: str = "app",
        guards: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sampling_rate: float = 1.0,
        watermark: bool = True,
    ) -> None:
        if not (0.0 <= sampling_rate <= 1.0):
            raise ValueError(
                f"sampling_rate must be between 0.0 and 1.0, got {sampling_rate}"
            )
        self._sink = sink or StdoutSink()
        self._service = _truncate_name(service)
        self._guards = guards or []
        self._metadata = metadata or {}
        self._sampling_rate = sampling_rate
        self._watermark = watermark
        self._watermark_emitted = False

    def __enter__(self) -> "Tracer":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if hasattr(self._sink, "shutdown"):
            self._sink.shutdown()
        return False

    @contextmanager
    def trace(self, name: str, data: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a new top-level trace span.

        If sampling_rate < 1.0, this trace may be silently skipped.
        The sampling decision is local to this trace — concurrent and
        nested traces do not interfere with each other.

        Args:
            name: Name of the trace span.
            data: Optional data to attach to the span.

        Yields:
            A TraceContext for creating child spans and events.
        """
        sampled = random.random() < self._sampling_rate
        ctx = TraceContext(
            tracer=self,
            trace_id=_new_id(),
            span_id=_new_id(),
            parent_id=None,
            name=_truncate_name(name),
            data=data,
            _sampled=sampled,
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
        Note: sampling is handled by TraceContext — if this method is
        called, the event should be emitted.
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
        if self._metadata:
            event["metadata"] = self._metadata
        if self._watermark and not self._watermark_emitted:
            self._watermark_emitted = True
            wm: Dict[str, Any] = {
                "service": self._service,
                "kind": "meta",
                "name": "watermark",
                "message": "Traced by AgentGuard | agentguard47.com",
                "ts": time.time(),
            }
            if self._metadata:
                wm["metadata"] = self._metadata
            self._sink.emit(wm)
        self._sink.emit(event)

        # Auto-check guards
        if kind == "event":
            self._check_guards(name, data)

    def _check_guards(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Run all attached guards. Called on every event, even sampled-out ones."""
        for guard in self._guards:
            if hasattr(guard, "auto_check"):
                guard.auto_check(name, data)
            elif hasattr(guard, "check"):
                # Backward compat: try check(name, data), then check()
                try:
                    guard.check(name, data)
                except TypeError:
                    try:
                        guard.check()
                    except TypeError:
                        pass

    def __repr__(self) -> str:
        return f"Tracer(service={self._service!r}, sink={self._sink!r}, watermark={self._watermark!r})"


def _new_id() -> str:
    return uuid.uuid4().hex
