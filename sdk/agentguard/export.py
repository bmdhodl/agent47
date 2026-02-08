"""Export trace data to various formats: JSON, CSV, JSONL.

Usage::

    from agentguard.export import export_json, export_csv

    export_json("traces.jsonl", "traces.json")
    export_csv("traces.jsonl", "traces.csv")
"""
from __future__ import annotations

import csv
import json
from typing import Any, Dict, List, Optional


def load_trace(path: str) -> List[Dict[str, Any]]:
    """Load events from a JSONL trace file.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of event dicts.
    """
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
    return events


def export_json(input_path: str, output_path: str) -> int:
    """Export JSONL trace to a single JSON array file.

    Args:
        input_path: Path to the JSONL trace file.
        output_path: Path for the output JSON file.

    Returns:
        Number of events exported.
    """
    events = load_trace(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, sort_keys=True)
    return len(events)


def export_csv(input_path: str, output_path: str, columns: Optional[List[str]] = None) -> int:
    """Export JSONL trace to CSV.

    Args:
        input_path: Path to the JSONL trace file.
        output_path: Path for the output CSV file.
        columns: Optional list of columns to include. Defaults to common fields.

    Returns:
        Number of rows exported.
    """
    events = load_trace(input_path)
    if not events:
        return 0

    if columns is None:
        columns = [
            "service", "kind", "phase", "name", "trace_id", "span_id",
            "parent_id", "ts", "duration_ms", "error",
        ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for event in events:
            # Flatten error to string
            row = dict(event)
            if "error" in row and isinstance(row["error"], dict):
                row["error"] = json.dumps(row["error"])
            writer.writerow(row)

    return len(events)


def export_jsonl(input_path: str, output_path: str) -> int:
    """Copy/normalize JSONL trace file (skip malformed lines).

    Args:
        input_path: Path to the input JSONL file.
        output_path: Path for the output JSONL file.

    Returns:
        Number of events exported.
    """
    events = load_trace(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, sort_keys=True) + "\n")
    return len(events)
