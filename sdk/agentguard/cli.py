from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any, Dict, List, Optional


def _summarize(path: str) -> None:
    total = 0
    name_counts = Counter()
    kind_counts = Counter()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event: Dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            name = event.get("name", "(unknown)")
            kind = event.get("kind", "(unknown)")
            name_counts[name] += 1
            kind_counts[kind] += 1

    print(f"events: {total}")
    print("kinds:")
    for kind, count in kind_counts.most_common():
        print(f"  {kind}: {count}")
    print("names:")
    for name, count in name_counts.most_common(10):
        print(f"  {name}: {count}")


def _report(path: str) -> None:
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not events:
        print("No events found.")
        return

    total = len(events)
    kinds = Counter(e.get("kind", "(unknown)") for e in events)
    names = Counter(e.get("name", "(unknown)") for e in events)
    loop_hits = names.get("guard.loop_detected", 0)

    span_durations: List[float] = []
    total_cost: float = 0.0
    for e in events:
        if e.get("kind") == "span" and e.get("phase") == "end":
            dur = e.get("duration_ms")
            if isinstance(dur, (int, float)):
                span_durations.append(float(dur))
        # Sum cost from top-level cost_usd field
        cost = e.get("cost_usd")
        if isinstance(cost, (int, float)):
            total_cost += float(cost)
        # Also check data.cost_usd (from instrument patches)
        data = e.get("data", {})
        if isinstance(data, dict):
            dcost = data.get("cost_usd")
            if isinstance(dcost, (int, float)):
                total_cost += float(dcost)

    total_ms: Optional[float] = None
    if span_durations:
        total_ms = max(span_durations)

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


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentguard")
    sub = parser.add_subparsers(dest="cmd")

    summarize = sub.add_parser("summarize", help="Summarize a JSONL trace file")
    summarize.add_argument("path")

    report = sub.add_parser("report", help="Human-readable report for a JSONL trace file")
    report.add_argument("path")

    view = sub.add_parser("view", help="Open a local trace viewer in the browser")
    view.add_argument("path")
    view.add_argument("--port", type=int, default=8080)
    view.add_argument("--no-open", action="store_true")

    eval_cmd = sub.add_parser("eval", help="Run evaluation assertions on a trace")
    eval_cmd.add_argument("path")
    eval_cmd.add_argument("--ci", action="store_true", help="CI mode: also assert no budget warnings")

    args = parser.parse_args()
    if args.cmd == "summarize":
        _summarize(args.path)
    elif args.cmd == "report":
        _report(args.path)
    elif args.cmd == "view":
        from agentguard.viewer import serve

        serve(args.path, port=args.port, open_browser=not args.no_open)
    elif args.cmd == "eval":
        _eval(args.path, ci=args.ci)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
