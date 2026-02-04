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
    for e in events:
        if e.get("kind") == "span" and e.get("phase") == "end":
            dur = e.get("duration_ms")
            if isinstance(dur, (int, float)):
                span_durations.append(float(dur))

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
    if loop_hits:
        print(f"  Loop guard triggered: {loop_hits} time(s)")
    else:
        print("  Loop guard triggered: 0")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentguard")
    sub = parser.add_subparsers(dest="cmd")

    summarize = sub.add_parser("summarize", help="Summarize a JSONL trace file")
    summarize.add_argument("path")

    report = sub.add_parser("report", help="Human-readable report for a JSONL trace file")
    report.add_argument("path")

    args = parser.parse_args()
    if args.cmd == "summarize":
        _summarize(args.path)
    elif args.cmd == "report":
        _report(args.path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
