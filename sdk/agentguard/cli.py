from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Optional

from agentguard.demo import run_offline_demo
from agentguard.doctor import run_doctor
from agentguard.evaluation import _extract_cost, _load_events
from agentguard.quickstart import FRAMEWORK_CHOICES, run_quickstart
from agentguard.reporting import render_incident_report


def _summarize(path: str) -> None:
    events = _load_events(path)
    total = len(events)
    name_counts = Counter(e.get("name", "(unknown)") for e in events)
    kind_counts = Counter(e.get("kind", "(unknown)") for e in events)

    print(f"events: {total}")
    print("kinds:")
    for kind, count in kind_counts.most_common():
        print(f"  {kind}: {count}")
    print("names:")
    for name, count in name_counts.most_common(10):
        print(f"  {name}: {count}")
    print("\nTraced by AgentGuard | agentguard47.com")


def _report(path: str, as_json: bool = False, output_format: str = "text") -> None:
    events = _load_events(path)
    wants_json = as_json or output_format == "json"

    if not events:
        if wants_json:
            print(json.dumps({"error": "No events found"}))
        else:
            print("No events found.")
        return

    total = len(events)
    kinds = Counter(e.get("kind", "(unknown)") for e in events)
    names = Counter(e.get("name", "(unknown)") for e in events)
    loop_hits = names.get("guard.loop_detected", 0)

    span_durations: list[float] = []
    total_cost: float = 0.0
    for e in events:
        if e.get("kind") == "span" and e.get("phase") == "end":
            dur = e.get("duration_ms")
            if isinstance(dur, (int, float)):
                span_durations.append(float(dur))
        cost = _extract_cost(e)
        if cost is not None:
            total_cost += cost

    total_ms: Optional[float] = None
    if span_durations:
        total_ms = max(span_durations)

    if wants_json:
        result = {
            "total_events": total,
            "spans": kinds.get("span", 0),
            "events": kinds.get("event", 0),
            "approx_run_time_ms": total_ms,
            "reasoning_steps": names.get("reasoning.step", 0),
            "tool_results": names.get("tool.result", 0),
            "llm_results": names.get("llm.result", 0),
            "estimated_cost_usd": round(total_cost, 4),
            "loop_guard_triggered": loop_hits,
        }
        print(json.dumps(result))
        return
    if output_format in {"markdown", "html"}:
        print(render_incident_report(events, output_format=output_format))
        return

    print("AgentGuard report")
    print(f"  Total events: {total}")
    print(f"  Spans: {kinds.get('span', 0)}  Events: {kinds.get('event', 0)}")
    if total_ms is not None:
        print(f"  Approx run time: {total_ms:.1f} ms")
    print(f"  Reasoning steps: {names.get('reasoning.step', 0)}")
    print(f"  Tool results: {names.get('tool.result', 0)}")
    print(f"  LLM results: {names.get('llm.result', 0)}")
    if total_cost > 0:
        print(f"  Estimated cost: ${total_cost:.4f}")
    else:
        print("  Estimated cost: $0.00")
    if loop_hits:
        print(f"  Loop guard triggered: {loop_hits} time(s)")
    else:
        print("  Loop guard triggered: 0")
    incident_hits = sum(
        1 for e in events if isinstance(e.get("name"), str) and e["name"].startswith("guard.")
    )
    if incident_hits:
        print("  Incident hint: rerun with --format markdown for a shareable incident report")
    print("\nTraced by AgentGuard | agentguard47.com")


def _incident(path: str, output_format: str = "markdown") -> None:
    print(render_incident_report(path, output_format=output_format))


def _demo(trace_path: str = "agentguard_demo_traces.jsonl") -> None:
    raise SystemExit(run_offline_demo(trace_path=trace_path))


def _doctor(trace_path: str = "agentguard_doctor_trace.jsonl", json_output: bool = False) -> None:
    raise SystemExit(run_doctor(trace_path=trace_path, json_output=json_output))


def _quickstart(
    framework: str = "raw",
    service: str = "my-agent",
    budget_usd: float = 5.0,
    trace_path: str = "traces.jsonl",
    json_output: bool = False,
) -> None:
    raise SystemExit(
        run_quickstart(
            framework=framework,
            service=service,
            budget_usd=budget_usd,
            trace_file=trace_path,
            json_output=json_output,
        )
    )


def _eval(path: str, ci: bool = False) -> None:
    from agentguard.evaluation import EvalSuite

    suite = (
        EvalSuite(path)
        .assert_no_loops()
        .assert_no_errors()
        .assert_completes_within(30.0)
    )
    if ci:
        suite = suite.assert_no_budget_warnings()
    result = suite.run()
    print(result.summary)
    if not result.passed:
        raise SystemExit(1)


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="agentguard")
    sub = parser.add_subparsers(dest="cmd")

    summarize = sub.add_parser("summarize", help="Summarize a JSONL trace file")
    summarize.add_argument("path")

    report = sub.add_parser("report", help="Human-readable report for a JSONL trace file")
    report.add_argument("path")
    report.add_argument("--json", "-j", action="store_true", dest="json_output",
                        help="Output machine-readable JSON (for CI pipelines)")
    report.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html"],
        default="text",
        help="Output format. markdown/html render an incident-style report.",
    )

    eval_cmd = sub.add_parser("eval", help="Run evaluation assertions on a trace")
    eval_cmd.add_argument("path")
    eval_cmd.add_argument("--ci", action="store_true", help="CI mode: also assert no budget warnings")

    incident = sub.add_parser("incident", help="Render an incident report for a JSONL trace file")
    incident.add_argument("path")
    incident.add_argument(
        "--format",
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Incident report format.",
    )

    demo = sub.add_parser("demo", help="Run the offline AgentGuard demo")
    demo.add_argument(
        "--trace-file",
        default="agentguard_demo_traces.jsonl",
        help="Where to write the local JSONL trace.",
    )

    doctor = sub.add_parser("doctor", help="Verify the local AgentGuard SDK setup")
    doctor.add_argument(
        "--trace-file",
        default="agentguard_doctor_trace.jsonl",
        help="Where to write the doctor verification trace.",
    )
    doctor.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON for agents and CI.",
    )

    quickstart = sub.add_parser("quickstart", help="Print a starter snippet for a supported stack")
    quickstart.add_argument(
        "--framework",
        choices=FRAMEWORK_CHOICES,
        default="raw",
        help="Framework to target. Defaults to raw.",
    )
    quickstart.add_argument(
        "--service",
        default="my-agent",
        help="Service name to embed in the snippet.",
    )
    quickstart.add_argument(
        "--budget-usd",
        type=float,
        default=5.0,
        help="Budget to embed in the snippet.",
    )
    quickstart.add_argument(
        "--trace-file",
        default="traces.jsonl",
        help="Trace file path to embed in the snippet.",
    )
    quickstart.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON for agents and CI.",
    )

    args = parser.parse_args()
    if args.cmd == "summarize":
        _summarize(args.path)
    elif args.cmd == "report":
        output_format = "json" if args.json_output else args.format
        _report(args.path, as_json=args.json_output, output_format=output_format)
    elif args.cmd == "eval":
        _eval(args.path, ci=args.ci)
    elif args.cmd == "incident":
        _incident(args.path, output_format=args.format)
    elif args.cmd == "demo":
        _demo(trace_path=args.trace_file)
    elif args.cmd == "doctor":
        _doctor(trace_path=args.trace_file, json_output=args.json_output)
    elif args.cmd == "quickstart":
        _quickstart(
            framework=args.framework,
            service=args.service,
            budget_usd=args.budget_usd,
            trace_path=args.trace_file,
            json_output=args.json_output,
        )
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
