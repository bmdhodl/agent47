"""Sticky local proof for a runaway CrewAI-style agent workflow.

Run:

    PYTHONPATH=sdk python examples/sticky_agent_proof.py --out-dir proof/sticky-agent-proof
    agentguard incident proof/sticky-agent-proof/sticky_agent_proof_traces.jsonl

No API keys, dashboard, framework installs, or network calls are required.
The optional hosted NDJSON output mirrors the shape posted by ``HttpSink`` so
the dashboard can validate the same proof contract.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, TextIO

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopDetected,
    LoopGuard,
    RetryGuard,
    RetryLimitExceeded,
    Tracer,
)
from agentguard.reporting import render_incident_report

DEFAULT_OUT_DIR = Path("sticky_agent_proof_output")
TRACE_NAME = "sticky_agent_proof_traces.jsonl"
HOSTED_NAME = "sticky_agent_proof_hosted.ndjson"
INCIDENT_NAME = "sticky_agent_proof_incident.md"
SERVICE = "crewai-vendor-review-sticky-proof"


def run_sticky_agent_proof(
    out_dir: Path | str = DEFAULT_OUT_DIR,
    stream: Optional[TextIO] = None,
) -> Dict[str, Path]:
    """Run a deterministic local proof and write trace, hosted, and incident files."""
    output = stream or sys.stdout
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    trace_path = out_path / TRACE_NAME
    hosted_path = out_path / HOSTED_NAME
    incident_path = out_path / INCIDENT_NAME
    for path in (trace_path, hosted_path, incident_path):
        if path.exists():
            path.unlink()

    tracer = Tracer(
        sink=JsonlFileSink(str(trace_path)),
        service=SERVICE,
        metadata={"framework": "crewai", "proof": "sticky-agent-proof"},
        watermark=False,
    )

    _print(output, "AgentGuard sticky agent proof")
    _print(output, "Synthetic CrewAI-style vendor review. No API keys. No network.")
    _run_retry_storm(tracer, output)
    _run_loop_detection(tracer, output)
    _run_budget_burn(tracer, output)
    _write_hosted_ndjson(trace_path, hosted_path)
    incident_path.write_text(
        render_incident_report(str(trace_path), output_format="markdown"),
        encoding="utf-8",
    )

    _print(output, "")
    _print(output, "Proof complete.")
    _print(output, f"Trace: {trace_path}")
    _print(output, f"Hosted NDJSON: {hosted_path}")
    _print(output, f"Incident: {incident_path}")
    return {
        "trace": trace_path,
        "hosted": hosted_path,
        "incident": incident_path,
    }


def _run_retry_storm(tracer: Tracer, out: TextIO) -> None:
    retry_guard = RetryGuard(max_retries=3)
    _print(out, "")
    _print(out, "1. RetryGuard: catching a clause lookup retry storm")
    with tracer.trace(
        "crewai.vendor_review.retry_storm",
        data={"crew": "vendor-review", "agent": "risk-reviewer"},
    ) as span:
        for attempt in range(1, 6):
            span.event(
                "tool.retry",
                data={
                    "framework": "crewai",
                    "agent": "risk-reviewer",
                    "task": "vendor-contract-review",
                    "tool_name": "clause_lookup",
                    "attempt": attempt,
                    "reason": "same upstream timeout",
                },
            )
            try:
                retry_guard.check("clause_lookup")
                _print(out, f"  clause_lookup retry {attempt} allowed")
            except RetryLimitExceeded as exc:
                span.event(
                    "guard.retry_limit_exceeded",
                    data={
                        "framework": "crewai",
                        "tool_name": "clause_lookup",
                        "attempt": attempt,
                        "message": str(exc),
                    },
                )
                _print(out, f"  stopped retry storm on attempt {attempt}: {exc}")
                return


def _run_loop_detection(tracer: Tracer, out: TextIO) -> None:
    loop_guard = LoopGuard(max_repeats=3, window=5)
    args = {"vendor": "acme-medical", "clause": "termination-for-convenience"}
    _print(out, "")
    _print(out, "2. LoopGuard: catching the same tool call repeating")
    with tracer.trace(
        "crewai.vendor_review.loop_detection",
        data={"crew": "vendor-review", "agent": "risk-reviewer"},
    ) as span:
        for attempt in range(1, 5):
            span.event(
                "tool.clause_lookup",
                data={
                    "framework": "crewai",
                    "agent": "risk-reviewer",
                    "task": "vendor-contract-review",
                    "tool_name": "clause_lookup",
                    "attempt": attempt,
                    "args": args,
                },
            )
            try:
                loop_guard.check("clause_lookup", args)
                _print(out, f"  repeated lookup {attempt} allowed")
            except LoopDetected as exc:
                span.event(
                    "guard.loop_detected",
                    data={
                        "framework": "crewai",
                        "tool_name": "clause_lookup",
                        "attempt": attempt,
                        "message": str(exc),
                    },
                )
                _print(out, f"  stopped repeated tool loop: {exc}")
                return


def _run_budget_burn(tracer: Tracer, out: TextIO) -> None:
    budget = BudgetGuard(max_cost_usd=0.05, warn_at_pct=0.8)
    costs = (0.013, 0.014, 0.014, 0.016)
    _print(out, "")
    _print(out, "3. BudgetGuard: stopping cost before it compounds")
    with tracer.trace(
        "crewai.vendor_review.budget_burn",
        data={"crew": "vendor-review", "agent": "risk-reviewer"},
    ) as span:
        for attempt, cost in enumerate(costs, 1):
            span.event(
                "llm.result",
                data={
                    "framework": "crewai",
                    "agent": "risk-reviewer",
                    "task": "vendor-contract-review",
                    "model": "gpt-4o",
                    "usage": {
                        "prompt_tokens": 1800 + attempt * 250,
                        "completion_tokens": 420,
                        "total_tokens": 2220 + attempt * 250,
                    },
                    "cost_usd": cost,
                },
                cost_usd=cost,
            )
            warned_before = budget._warned
            try:
                budget.consume(tokens=2220 + attempt * 250, calls=1, cost_usd=cost)
                _print(out, f"  model call {attempt}: ${budget.state.cost_used:.3f} used")
            except BudgetExceeded as exc:
                span.event(
                    "guard.budget_exceeded",
                    data={
                        "framework": "crewai",
                        "attempt": attempt,
                        "message": str(exc),
                        "cost_used": round(budget.state.cost_used, 6),
                        "limit_usd": budget.max_cost_usd,
                    },
                )
                _print(out, f"  stopped budget burn: {exc}")
                return
            if not warned_before and budget._warned:
                span.event(
                    "guard.budget_warning",
                    data={
                        "framework": "crewai",
                        "cost_used": round(budget.state.cost_used, 6),
                        "limit_usd": budget.max_cost_usd,
                    },
                )
                _print(out, f"  budget warning at ${budget.state.cost_used:.3f}")


def _write_hosted_ndjson(trace_path: Path, hosted_path: Path) -> None:
    with trace_path.open(encoding="utf-8") as source, hosted_path.open(
        "w",
        encoding="utf-8",
    ) as target:
        for event in _hosted_events(source):
            target.write(json.dumps(event, sort_keys=True) + "\n")


def _hosted_events(lines: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for line in lines:
        if not line.strip():
            continue
        event = json.loads(line)
        kind = event.get("kind")
        if kind not in {"span", "event"}:
            continue
        hosted_event = dict(event)
        hosted_event.setdefault("type", kind)
        yield hosted_event


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Directory for trace, hosted NDJSON, and incident artifacts.",
    )
    args = parser.parse_args(argv)
    run_sticky_agent_proof(Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
