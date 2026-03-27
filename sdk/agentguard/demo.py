from __future__ import annotations

import os
import sys
from typing import Optional, TextIO

from agentguard.guards import (
    BudgetExceeded,
    BudgetGuard,
    LoopDetected,
    LoopGuard,
    RetryGuard,
    RetryLimitExceeded,
)
from agentguard.tracing import JsonlFileSink, Tracer

_BUDGET_STEPS = (0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)


def run_offline_demo(
    trace_path: str = "agentguard_demo_traces.jsonl",
    stream: Optional[TextIO] = None,
) -> int:
    """Run a deterministic local demo that proves AgentGuard enforcement.

    The demo is intentionally offline and dependency-free:
    - no API keys
    - no network access
    - no dashboard required

    It demonstrates three concrete failure modes:
    - BudgetGuard stopping runaway spend
    - LoopGuard stopping repeated tool calls
    - RetryGuard stopping retry storms

    Args:
        trace_path: Where to write the JSONL trace.
        stream: Optional text stream for human-readable output.

    Returns:
        Process-style exit code. ``0`` means the demo completed successfully.
    """
    out = stream or sys.stdout
    if os.path.exists(trace_path):
        os.remove(trace_path)

    tracer = Tracer(
        sink=JsonlFileSink(trace_path),
        service="agentguard-offline-demo",
        guards=[LoopGuard(max_repeats=3, window=6), RetryGuard(max_retries=2)],
        watermark=False,
    )

    _print(out, "AgentGuard offline demo")
    _print(out, "No API keys. No dashboard. No network calls.")
    _print(out, "")

    _run_budget_demo(tracer, out)
    _print(out, "")
    _run_loop_demo(tracer, out)
    _print(out, "")
    _run_retry_demo(tracer, out)
    _print(out, "")
    _print(out, "Local proof complete.")
    _print(out, f"Trace written to: {trace_path}")
    _print(out, f"View summary: agentguard report {trace_path}")
    _print(out, f"View incident report: agentguard incident {trace_path}")
    _print(out, "SDK gives you local enforcement. The dashboard adds alerts, retained history, and remote controls.")
    return 0


def _run_budget_demo(tracer: Tracer, out: TextIO) -> None:
    budget = BudgetGuard(
        max_cost_usd=1.00,
        warn_at_pct=0.8,
        on_warning=lambda msg: _print(out, f"  warning: {msg}"),
    )
    _print(out, "1. BudgetGuard: stopping runaway spend")
    with tracer.trace("demo.budget_guard") as span:
        for idx, cost in enumerate(_BUDGET_STEPS, 1):
            span.event("reasoning.step", data={"step": idx, "thought": "issuing another model call"})
            span.event(
                "llm.result",
                data={"model": "offline-demo-model", "usage": {"total_tokens": 500}},
                cost_usd=cost,
            )
            warned_before = budget._warned
            try:
                budget.consume(tokens=500, calls=1, cost_usd=cost)
            except BudgetExceeded as exc:
                span.event(
                    "guard.budget_exceeded",
                    data={
                        "message": str(exc),
                        "cost_used": round(budget.state.cost_used, 4),
                        "limit_usd": budget.max_cost_usd,
                    },
                )
                _print(
                    out,
                    f"  stopped on call {idx}: cost ${budget.state.cost_used:.2f} exceeded ${budget.max_cost_usd:.2f}",
                )
                return
            if not warned_before and budget._warned:
                span.event(
                    "guard.budget_warning",
                    data={
                        "cost_used": round(budget.state.cost_used, 4),
                        "limit_usd": budget.max_cost_usd,
                    },
                )
                _print(out, f"  warning fired at ${budget.state.cost_used:.2f}")


def _run_loop_demo(tracer: Tracer, out: TextIO) -> None:
    _print(out, "2. LoopGuard: stopping repeated tool calls")
    with tracer.trace("demo.loop_guard") as span:
        for attempt in range(1, 5):
            try:
                span.event("tool.search", data={"query": "python asyncio"})
                _print(out, f"  tool.search attempt {attempt} allowed")
            except LoopDetected as exc:
                span.event(
                    "guard.loop_detected",
                    data={"message": str(exc), "tool_name": "search"},
                )
                _print(out, f"  stopped on repeated tool call: {exc}")
                return


def _run_retry_demo(tracer: Tracer, out: TextIO) -> None:
    _print(out, "3. RetryGuard: stopping retry storms")
    with tracer.trace("demo.retry_guard") as span:
        for attempt in range(1, 5):
            try:
                span.event("tool.retry", data={"tool_name": "fetch_docs", "attempt": attempt})
                span.event(
                    "tool.error",
                    data={
                        "tool_name": "fetch_docs",
                        "error_type": "TimeoutError",
                        "message": f"upstream timeout on attempt {attempt}",
                    },
                )
                _print(out, f"  fetch_docs retry {attempt} allowed")
            except RetryLimitExceeded as exc:
                span.event(
                    "guard.retry_limit_exceeded",
                    data={"message": str(exc), "tool_name": "fetch_docs"},
                )
                _print(out, f"  stopped retry storm: {exc}")
                return


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")


def main() -> None:  # pragma: no cover
    raise SystemExit(run_offline_demo())


if __name__ == "__main__":  # pragma: no cover
    main()
