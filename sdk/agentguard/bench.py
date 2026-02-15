"""Benchmark script for AgentGuard SDK overhead measurement.

Run with:
    python -m agentguard.bench

Measures the overhead of core operations (tracing, guards, sinks)
to verify < 0.1ms per operation.
"""
from __future__ import annotations

import time
from typing import Any, Dict


def _bench(name: str, fn, iterations: int = 10000) -> float:  # pragma: no cover
    """Run fn() for iterations and return avg time in microseconds."""
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    avg_us = (elapsed / iterations) * 1_000_000
    print(f"  {name}: {avg_us:.2f} µs/op ({iterations} iterations, {elapsed:.3f}s total)")
    return avg_us


class _NullSink:  # pragma: no cover
    """Sink that discards events (for measuring tracer overhead only)."""
    def emit(self, event: Dict[str, Any]) -> None:
        pass


def main() -> None:  # pragma: no cover
    from agentguard.guards import BudgetGuard, LoopGuard
    from agentguard.tracing import JsonlFileSink, Tracer

    print("AgentGuard SDK Benchmark")
    print("=" * 50)

    # 1. Tracer overhead (null sink)
    print("\nTracer (NullSink):")
    tracer = Tracer(sink=_NullSink(), service="bench")

    def trace_span():
        with tracer.trace("bench.span") as ctx:
            ctx.event("bench.event", data={"key": "value"})

    _bench("trace + event", trace_span)

    # 2. Event-only overhead
    print("\nEvent emission:")
    def emit_event():
        tracer._emit(
            kind="event", phase="emit", trace_id="t1", span_id="s1",
            parent_id=None, name="bench.event", data={"key": "value"},
        )
    _bench("_emit", emit_event, iterations=50000)

    # 3. LoopGuard.check
    print("\nLoopGuard:")
    guard = LoopGuard(max_repeats=100, window=200)
    counter = [0]
    def loop_check():
        counter[0] += 1
        try:
            guard.check(f"tool_{counter[0] % 50}", {"i": counter[0]})
        except Exception:
            guard.reset()
    _bench("check", loop_check, iterations=50000)

    # 4. BudgetGuard.consume
    print("\nBudgetGuard:")
    budget = BudgetGuard(max_tokens=1_000_000_000)
    def budget_consume():
        budget.consume(tokens=1, calls=0, cost_usd=0.0)
    _bench("consume", budget_consume, iterations=50000)

    # 5. JsonlFileSink
    print("\nJsonlFileSink (write):")
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    sink = JsonlFileSink(path)
    event = {"service": "bench", "name": "test", "ts": time.time(), "data": {}}
    def sink_write():
        sink.emit(event)
    _bench("emit", sink_write, iterations=5000)
    # Cleanup
    size = os.path.getsize(path)
    os.unlink(path)
    print(f"  (wrote {size:,} bytes)")

    # Summary
    print("\n" + "=" * 50)
    print("Target: < 100 µs (0.1ms) per operation")
    print("Done.")


if __name__ == "__main__":  # pragma: no cover
    main()
