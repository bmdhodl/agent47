from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TextIO

from agentguard import BudgetGuard, JsonlFileSink, LoopDetected, LoopGuard, RetryGuard, RetryLimitExceeded, Tracer, trace_agent, trace_tool
from agentguard.sinks.http import HttpSink
from agentguard.tracing import TraceSink

DEFAULT_SERVICE = "smoke-coding-agent"
DEFAULT_TRACE_FILE = ".agentguard/smoke_coding_agent_traces.jsonl"
DEFAULT_DASHBOARD_URL = "https://app.agentguard47.com"

_DOC_SNIPPETS = {
    "doctor": "Run agentguard doctor first. It stays local, writes a trace, and confirms the SDK path before you touch a real agent.",
    "demo": "Run agentguard demo next. It proves budget, loop, and retry enforcement locally with no API keys or dashboard required.",
    "quickstart": "Use agentguard quickstart --framework <stack> to print the smallest credible starter snippet for your real stack.",
    "config": "Commit a tiny .agentguard.json with profile='coding-agent', a local trace path, and a small budget so humans and coding agents share safe defaults.",
}


class MirrorSink(TraceSink):
    """Emit identical events to multiple sinks."""

    def __init__(self, *sinks: TraceSink) -> None:
        self._sinks = sinks

    def emit(self, event: Dict[str, Any]) -> None:
        for sink in self._sinks:
            sink.emit(event)

    def shutdown(self) -> None:
        for sink in self._sinks:
            shutdown = getattr(sink, "shutdown", None)
            if callable(shutdown):
                shutdown()


def run_smoke_agent(
    *,
    trace_file: str = DEFAULT_TRACE_FILE,
    service: str = DEFAULT_SERVICE,
    dashboard: bool = False,
    api_key: Optional[str] = None,
    dashboard_url: Optional[str] = None,
    stream: Optional[TextIO] = None,
    _allow_private_dashboard_url: bool = False,
) -> Dict[str, Any]:
    """Run a scratch coding-agent smoke test from the SDK up."""
    out = stream
    trace_path = Path(trace_file)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    if trace_path.exists():
        trace_path.unlink()

    resolved_api_key = api_key or os.environ.get("AGENTGUARD_API_KEY")
    resolved_dashboard_url = (
        (dashboard_url or os.environ.get("AGENTGUARD_DASHBOARD_URL") or DEFAULT_DASHBOARD_URL)
        .rstrip("/")
    )

    if dashboard and not resolved_api_key:
        raise RuntimeError("dashboard=True requires AGENTGUARD_API_KEY or an explicit api_key")

    sinks: List[TraceSink] = [JsonlFileSink(str(trace_path))]
    if dashboard:
        sinks.append(
            HttpSink(
                url=f"{resolved_dashboard_url}/api/ingest",
                api_key=resolved_api_key,
                batch_size=5,
                flush_interval=0.2,
                _allow_private=_allow_private_dashboard_url,
            )
        )

    sink = MirrorSink(*sinks)
    loop_guard = LoopGuard(max_repeats=3, window=6)
    retry_guard = RetryGuard(max_retries=2)
    budget_guard = BudgetGuard(max_cost_usd=1.0, warn_at_pct=0.8)

    tracer = Tracer(
        sink=sink,
        service=service,
        guards=[retry_guard, budget_guard],
        watermark=False,
    )

    trace_ids: Dict[str, Optional[str]] = {"healthy": None, "loop": None, "retry": None}

    @trace_tool(tracer)
    def search_setup_steps(topic: str) -> str:
        del topic
        return " ".join(
            [
                _DOC_SNIPPETS["doctor"],
                _DOC_SNIPPETS["demo"],
                _DOC_SNIPPETS["quickstart"],
                _DOC_SNIPPETS["config"],
            ]
        )

    @trace_tool(tracer)
    def draft_local_only_answer(user_request: str, evidence: str) -> str:
        del user_request
        return (
            "Local-first AgentGuard setup:\n"
            "1. Add .agentguard.json with profile='coding-agent' and .agentguard/traces.jsonl.\n"
            "2. Run agentguard doctor.\n"
            "3. Run agentguard demo.\n"
            "4. Run agentguard quickstart --framework raw or your real stack.\n"
            "5. Keep the first integration local_only=True until the trace path is proven.\n"
            f"Evidence: {evidence}"
        )

    @trace_tool(tracer)
    def flaky_context_lookup(topic: str) -> str:
        raise TimeoutError(f"simulated upstream timeout while looking up {topic}")

    @trace_agent(tracer, name="agent.answer_user")
    def answer_user(user_request: str, _trace_ctx: Optional[Any] = None) -> str:
        trace_ids["healthy"] = getattr(_trace_ctx, "trace_id", None)
        if _trace_ctx is not None:
            _trace_ctx.event(
                "agent.user_request",
                data={"persona": "developer", "request": user_request[:500]},
            )
            _trace_ctx.event(
                "reasoning.step",
                data={"thought": "Collect the safest local-only setup steps first."},
            )
        evidence = search_setup_steps("local-first coding-agent onboarding")
        if _trace_ctx is not None:
            _trace_ctx.event(
                "reasoning.step",
                data={"thought": "Draft a deterministic answer that never requires the dashboard first."},
            )
        answer = draft_local_only_answer(user_request, evidence)
        if _trace_ctx is not None:
            _trace_ctx.event(
                "llm.result",
                data={
                    "model": "smoke-local-model",
                    "usage": {"input_tokens": 320, "output_tokens": 95, "total_tokens": 415},
                },
                cost_usd=0.0012,
            )
            _trace_ctx.event("agent.answer", data={"answer": answer[:500]})
        return answer

    @trace_agent(tracer, name="agent.loop_probe")
    def trigger_loop(_trace_ctx: Optional[Any] = None) -> None:
        trace_ids["loop"] = getattr(_trace_ctx, "trace_id", None)
        if _trace_ctx is not None:
            _trace_ctx.event(
                "agent.user_request",
                data={"persona": "developer", "request": "Find the same setup step until you are sure."},
            )
        for attempt in range(1, 6):
            if _trace_ctx is not None:
                _trace_ctx.event(
                    "reasoning.step",
                    data={"thought": f"Repeat the same repo lookup again (attempt {attempt})."},
                )
            try:
                if _trace_ctx is None:
                    raise RuntimeError("trace context missing")
                _trace_ctx.event(
                    "tool.call",
                    data={
                        "tool": "repo_lookup",
                        "query": "local-only setup",
                        "attempt": attempt,
                    },
                )
                loop_guard.check("repo_lookup", {"query": "local-only setup"})
            except LoopDetected as exc:
                if _trace_ctx is not None:
                    _trace_ctx.event(
                        "guard.loop_detected",
                        data={"message": str(exc), "attempt": attempt},
                    )
                raise

    @trace_agent(tracer, name="agent.retry_probe")
    def trigger_retry_guard(_trace_ctx: Optional[Any] = None) -> None:
        trace_ids["retry"] = getattr(_trace_ctx, "trace_id", None)
        if _trace_ctx is not None:
            _trace_ctx.event(
                "agent.user_request",
                data={"persona": "developer", "request": "Retry the same flaky lookup until it works."},
            )
        for attempt in range(1, 5):
            if _trace_ctx is not None:
                _trace_ctx.event(
                    "reasoning.step",
                    data={"thought": f"Try the flaky context lookup again (attempt {attempt})."},
                )
            try:
                flaky_context_lookup("dashboard verification")
            except RetryLimitExceeded as exc:
                if _trace_ctx is not None:
                    _trace_ctx.event(
                        "guard.retry_limit_exceeded",
                        data={"message": str(exc), "attempt": attempt},
                    )
                raise
            except TimeoutError:
                continue

    healthy_answer = answer_user(
        "I am wiring AgentGuard into my coding agent. Show me the safest local-first setup and how to verify it."
    )

    loop_triggered = False
    loop_message = ""
    try:
        trigger_loop()
    except LoopDetected as exc:
        loop_triggered = True
        loop_message = str(exc)

    retry_triggered = False
    retry_message = ""
    try:
        trigger_retry_guard()
    except RetryLimitExceeded as exc:
        retry_triggered = True
        retry_message = str(exc)

    sink.shutdown()

    summary = {
        "status": "ok",
        "service": service,
        "trace_file": str(trace_path),
        "dashboard_enabled": dashboard,
        "dashboard_url": resolved_dashboard_url if dashboard else None,
        "healthy_trace_id": trace_ids["healthy"],
        "loop_trace_id": trace_ids["loop"],
        "retry_trace_id": trace_ids["retry"],
        "healthy_answer": healthy_answer,
        "loop_guard_triggered": loop_triggered,
        "loop_guard_message": loop_message,
        "retry_guard_triggered": retry_triggered,
        "retry_guard_message": retry_message,
        "report_command": f"agentguard report {trace_path}",
        "incident_command": f"agentguard incident {trace_path}",
    }

    if out is not None:
        _render_text(summary, out)

    return summary


def _render_text(summary: Dict[str, Any], out: TextIO) -> None:
    out.write("Scratch coding-agent smoke test\n")
    out.write(f"Service: {summary['service']}\n")
    out.write(f"Trace file: {summary['trace_file']}\n")
    out.write(f"Dashboard mirror: {'enabled' if summary['dashboard_enabled'] else 'disabled'}\n")
    out.write("\nHealthy answer:\n")
    out.write(summary["healthy_answer"] + "\n")
    out.write("\nRuntime enforcement:\n")
    out.write(f"  LoopGuard triggered: {summary['loop_guard_triggered']}\n")
    out.write(f"  RetryGuard triggered: {summary['retry_guard_triggered']}\n")
    out.write("\nNext commands:\n")
    out.write(f"  {summary['report_command']}\n")
    out.write(f"  {summary['incident_command']}\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the scratch coding-agent smoke test.")
    parser.add_argument(
        "--trace-file",
        default=DEFAULT_TRACE_FILE,
        help="Where to write the local JSONL trace file.",
    )
    parser.add_argument(
        "--service",
        default=DEFAULT_SERVICE,
        help="Service name attached to every emitted event.",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Mirror the same trace stream to the hosted dashboard using AGENTGUARD_API_KEY.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON instead of the human summary.",
    )
    args = parser.parse_args(argv)

    summary = run_smoke_agent(
        trace_file=args.trace_file,
        service=args.service,
        dashboard=args.dashboard,
        stream=None if args.json_output else None,
    )

    if args.json_output:
        print(json.dumps(summary))
    else:
        _render_text(summary, out=sys.stdout)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
