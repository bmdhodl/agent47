from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import threading
import time
import uuid


class TraceSink:
    def emit(self, event: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class StdoutSink(TraceSink):
    def emit(self, event: Dict[str, Any]) -> None:
        print(json.dumps(event, sort_keys=True))


class JsonlFileSink(TraceSink):
    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()

    def emit(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, sort_keys=True)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


@dataclass
class TraceContext:
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
        """Lazy-initialized CostTracker for this trace."""
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
        return TraceContext(
            tracer=self.tracer,
            trace_id=self.trace_id,
            span_id=_new_id(),
            parent_id=self.span_id,
            name=name,
            data=data,
        )

    def event(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
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
    def __init__(self, sink: Optional[TraceSink] = None, service: str = "app") -> None:
        self._sink = sink or StdoutSink()
        self._service = service

    @contextmanager
    def trace(self, name: str, data: Optional[Dict[str, Any]] = None) -> TraceContext:
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


def _new_id() -> str:
    return uuid.uuid4().hex
