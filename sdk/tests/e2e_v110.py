#!/usr/bin/env python3
"""End-to-end verification of SDK v1.1.0 features.

Simulates a real multi-tool agent that:
1. Uses Tracer context manager (auto-shutdown)
2. Uses TimeoutGuard context manager
3. Uses BaseGuard subclass (custom guard)
4. Uses BudgetGuard (thread-safe)
5. Runs tools across threads (concurrency)
6. Generates traces to JSONL
7. Summarizes with summarize_trace()
8. Runs CLI report
9. Verifies guard auto_check dispatch
10. Tests name truncation on long names
"""
import json
import os
import sys
import tempfile
import threading
import time

# Ensure we import from the local SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentguard import (
    BaseGuard,
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopDetected,
    LoopGuard,
    TimeoutExceeded,
    TimeoutGuard,
    Tracer,
    summarize_trace,
)

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


def main():
    global PASS, FAIL
    trace_path = tempfile.mktemp(suffix=".jsonl")

    print("=" * 60)
    print("SDK v1.1.0 End-to-End Verification")
    print("=" * 60)

    # ── 1. Tracer context manager + basic tracing ──────────────
    print("\n1. Tracer context manager + basic tracing")
    sink = JsonlFileSink(trace_path)
    with Tracer(sink=sink, service="e2e-test") as tracer:
        with tracer.trace("agent.research") as ctx:
            ctx.event("reasoning.step", data={"thought": "search for docs"})
            with ctx.span("tool.search") as child:
                time.sleep(0.01)
                child.event("tool.result", data={"found": 3})
            with ctx.span("tool.summarize") as child:
                time.sleep(0.01)
                child.event("tool.result", data={"summary": "done"})

    # Verify trace file exists and has events
    with open(trace_path, "r") as f:
        events = [json.loads(l) for l in f if l.strip()]
    check("Trace file written", len(events) > 0, f"got {len(events)} events")
    check("Has span events", any(e["kind"] == "span" for e in events))
    check("Has point events", any(e["kind"] == "event" for e in events))
    check("Service name correct", all(e["service"] == "e2e-test" for e in events))

    # ── 2. summarize_trace() ──────────────────────────────────
    print("\n2. summarize_trace() API")
    summary = summarize_trace(trace_path)
    check("total_events > 0", summary["total_events"] > 0, f"got {summary['total_events']}")
    check("spans > 0", summary["spans"] > 0, f"got {summary['spans']}")
    check("events > 0", summary["events"] > 0, f"got {summary['events']}")
    check("duration_ms > 0", summary["duration_ms"] > 0, f"got {summary['duration_ms']}")
    check("tool_calls counted", summary["tool_calls"] == 2, f"got {summary['tool_calls']}")
    check("errors = 0", summary["errors"] == 0)

    # Also test with list input
    summary2 = summarize_trace(events)
    check("summarize_trace(list) works", summary2["total_events"] == summary["total_events"])

    # ── 3. TimeoutGuard context manager ───────────────────────
    print("\n3. TimeoutGuard context manager")
    with TimeoutGuard(max_seconds=5.0) as guard:
        time.sleep(0.01)
        guard.check()
    check("TimeoutGuard CM — no timeout", True)

    timed_out = False
    try:
        with TimeoutGuard(max_seconds=0.01) as guard:
            time.sleep(0.05)
    except TimeoutExceeded:
        timed_out = True
    check("TimeoutGuard CM — timeout fires", timed_out)

    # ── 4. BaseGuard subclass + auto_check ────────────────────
    print("\n4. BaseGuard subclass + auto_check dispatch")

    class ToolBlocker(BaseGuard):
        """Custom guard that blocks a specific tool."""
        def __init__(self, blocked_tool):
            self.blocked_tool = blocked_tool
            self.checked = []

        def auto_check(self, event_name, event_data=None):
            self.checked.append(event_name)
            if event_name == self.blocked_tool:
                raise RuntimeError(f"Tool {event_name} is blocked!")

    blocker = ToolBlocker("tool.dangerous")
    trace_path2 = tempfile.mktemp(suffix=".jsonl")

    blocked = False
    with Tracer(sink=JsonlFileSink(trace_path2), guards=[blocker]) as tracer:
        with tracer.trace("agent.test") as ctx:
            ctx.event("tool.safe")  # should pass
            try:
                ctx.event("tool.dangerous")  # should trigger blocker
            except RuntimeError:
                blocked = True

    check("Custom guard auto_check called", len(blocker.checked) >= 1)
    check("Safe tool passed", "tool.safe" in blocker.checked)
    check("Dangerous tool blocked", blocked)
    os.unlink(trace_path2)

    # ── 5. LoopGuard auto_check via Tracer ────────────────────
    print("\n5. LoopGuard auto_check via Tracer")
    trace_path3 = tempfile.mktemp(suffix=".jsonl")
    loop_guard = LoopGuard(max_repeats=3)

    loop_caught = False
    with Tracer(sink=JsonlFileSink(trace_path3), guards=[loop_guard]) as tracer:
        with tracer.trace("agent.loop-test") as ctx:
            try:
                for _ in range(5):
                    ctx.event("tool.search", data={"q": "same"})
            except LoopDetected:
                loop_caught = True

    check("LoopGuard fires via auto_check", loop_caught)
    os.unlink(trace_path3)

    # ── 6. BudgetGuard thread safety ──────────────────────────
    print("\n6. BudgetGuard thread safety (10 threads)")
    guard = BudgetGuard(max_cost_usd=100.0)
    barrier = threading.Barrier(10)

    def consume_budget():
        barrier.wait()
        for _ in range(100):
            guard.consume(cost_usd=0.01)

    threads = [threading.Thread(target=consume_budget) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = 10.0
    actual = guard.state.cost_used
    check(
        f"Thread-safe total: ${actual:.2f} == ${expected:.2f}",
        abs(actual - expected) < 0.01,
        f"got ${actual:.4f}",
    )

    # ── 7. BudgetGuard exceed under concurrency ───────────────
    print("\n7. BudgetGuard exceed under concurrency")
    guard2 = BudgetGuard(max_tokens=500)
    exceeded_count = 0
    lock = threading.Lock()

    def consume_tokens():
        nonlocal exceeded_count
        for _ in range(100):
            try:
                guard2.consume(tokens=1)
            except BudgetExceeded:
                with lock:
                    exceeded_count += 1

    threads = [threading.Thread(target=consume_tokens) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    check("Budget exceeded fired", exceeded_count > 0, f"exceeded {exceeded_count} times")
    check("Total tokens >= 500", guard2.state.tokens_used >= 500, f"got {guard2.state.tokens_used}")

    # ── 8. Name truncation ────────────────────────────────────
    print("\n8. Name truncation (1000 char limit)")
    trace_path4 = tempfile.mktemp(suffix=".jsonl")
    long_name = "x" * 2000

    with Tracer(sink=JsonlFileSink(trace_path4), service="truncation-test") as tracer:
        with tracer.trace(long_name) as ctx:
            ctx.event(long_name, data={"test": True})

    with open(trace_path4, "r") as f:
        trunc_events = [json.loads(l) for l in f if l.strip()]

    all_names_ok = all(len(e["name"]) <= 1000 for e in trunc_events)
    check("All names <= 1000 chars", all_names_ok)
    os.unlink(trace_path4)

    # ── 9. CLI report ─────────────────────────────────────────
    print("\n9. CLI report on trace file")
    from agentguard.cli import _report, _summarize
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        _report(trace_path)
    output = buf.getvalue()
    check("CLI report runs", "Total events" in output, output[:100])

    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        _summarize(trace_path)
    output2 = buf2.getvalue()
    check("CLI summarize runs", "events:" in output2, output2[:100])

    # ── 10. Eval suite on generated trace ─────────────────────
    print("\n10. EvalSuite on generated trace")
    from agentguard import EvalSuite
    result = (
        EvalSuite(trace_path)
        .assert_no_loops()
        .assert_no_errors()
        .assert_completes_within(10.0)
        .run()
    )
    check("EvalSuite all passed", result.passed, result.summary)

    # ── Cleanup ───────────────────────────────────────────────
    os.unlink(trace_path)

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} passed, {FAIL} failed")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
    print("\nAll v1.1.0 features verified end-to-end.")


if __name__ == "__main__":
    main()
