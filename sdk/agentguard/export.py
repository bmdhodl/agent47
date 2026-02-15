"""Export trace data to various formats: JSON, CSV, JSONL, OTLP.

Usage::

    from agentguard.export import export_json, export_csv, export_otlp

    export_json("traces.jsonl", "traces.json")
    export_csv("traces.jsonl", "traces.csv")
    export_otlp("traces.jsonl", "traces_otlp.json")
"""
from __future__ import annotations

import csv
import json
from typing import Any, Dict, List, Optional, Tuple


def load_trace(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
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


def export_otlp(
    input_path: str,
    output_path: str,
    service_name: Optional[str] = None,
) -> int:
    """Export JSONL trace to OTLP-compatible JSON (OpenTelemetry Protocol).

    Produces a JSON file conforming to the OTLP/JSON trace export format
    (``ExportTraceServiceRequest``). Compatible with OpenTelemetry Collector
    HTTP receivers and any tool that ingests OTLP JSON.

    Args:
        input_path: Path to the JSONL trace file.
        output_path: Path for the output OTLP JSON file.
        service_name: Service name for the resource. Defaults to event service field.

    Returns:
        Number of spans exported.

    Example::

        # Export and send to an OTel collector:
        export_otlp("traces.jsonl", "otlp.json")
        # Then: curl -X POST http://collector:4318/v1/traces -H 'Content-Type: application/json' -d @otlp.json
    """
    events = load_trace(input_path)
    return _write_otlp(events, output_path, service_name)


def events_to_otlp(
    events: List[Dict[str, Any]],
    service_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a list of AgentGuard events to an OTLP JSON structure in memory.

    Args:
        events: List of AgentGuard event dicts.
        service_name: Service name for the resource.

    Returns:
        OTLP ExportTraceServiceRequest dict.
    """
    return _build_otlp(events, service_name)


def _write_otlp(
    events: List[Dict[str, Any]],
    output_path: str,
    service_name: Optional[str] = None,
) -> int:
    """Build OTLP structure and write to file."""
    otlp = _build_otlp(events, service_name)
    span_count = sum(
        len(ss.get("spans", []))
        for rs in otlp.get("resourceSpans", [])
        for ss in rs.get("scopeSpans", [])
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(otlp, f, indent=2)
    return span_count


def _build_otlp(
    events: List[Dict[str, Any]],
    service_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Build an OTLP ExportTraceServiceRequest from AgentGuard events.

    Groups events by trace_id, reconstructs spans from start/end pairs,
    and formats according to the OTLP JSON spec.
    """
    # Group span events by (trace_id, span_id)
    span_starts: Dict[Tuple[str, str], Dict[str, Any]] = {}
    span_ends: Dict[Tuple[str, str], Dict[str, Any]] = {}
    point_events: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    svc = service_name
    for event in events:
        if not svc:
            svc = event.get("service", "agentguard")

        trace_id = event.get("trace_id", "")
        span_id = event.get("span_id", "")
        kind = event.get("kind")
        phase = event.get("phase")
        key = (trace_id, span_id)

        if kind == "span" and phase == "start":
            span_starts[key] = event
        elif kind == "span" and phase == "end":
            span_ends[key] = event
        elif kind == "event":
            parent_id = event.get("parent_id", span_id)
            parent_key = (trace_id, parent_id)
            point_events.setdefault(parent_key, []).append(event)

    svc = svc or "agentguard"

    # Build OTLP spans
    otlp_spans: List[Dict[str, Any]] = []
    for key, start_evt in span_starts.items():
        trace_id, span_id = key
        end_evt = span_ends.get(key, {})

        start_ns = _sec_to_nano(start_evt.get("ts", 0))
        duration_ms = end_evt.get("duration_ms", 0)
        end_ns = start_ns + int((duration_ms or 0) * 1_000_000)

        # Build attributes from data
        attributes = []
        data = start_evt.get("data", {})
        if isinstance(data, dict):
            for k, v in data.items():
                attributes.append(_kv(k, v))

        # Add cost if present
        cost = end_evt.get("cost_usd")
        if cost is not None:
            attributes.append(_kv("cost_usd", cost))

        # Build events
        otlp_events = []
        for pe in point_events.get(key, []):
            evt_attrs = []
            pe_data = pe.get("data", {})
            if isinstance(pe_data, dict):
                for k, v in pe_data.items():
                    evt_attrs.append(_kv(k, v))
            otlp_events.append({
                "timeUnixNano": str(_sec_to_nano(pe.get("ts", 0))),
                "name": pe.get("name", "event"),
                "attributes": evt_attrs,
            })

        # Build status
        error = end_evt.get("error")
        status: Dict[str, Any]
        if error:
            status = {
                "code": 2,  # STATUS_CODE_ERROR
                "message": str(error.get("message", "")),
            }
        else:
            status = {"code": 1}  # STATUS_CODE_OK

        otlp_span: Dict[str, Any] = {
            "traceId": _hex_pad(trace_id, 32),
            "spanId": _hex_pad(span_id, 16),
            "name": start_evt.get("name", "unknown"),
            "kind": 1,  # SPAN_KIND_INTERNAL
            "startTimeUnixNano": str(start_ns),
            "endTimeUnixNano": str(end_ns),
            "attributes": attributes,
            "events": otlp_events,
            "status": status,
        }

        parent_id = start_evt.get("parent_id")
        if parent_id:
            otlp_span["parentSpanId"] = _hex_pad(parent_id, 16)

        otlp_spans.append(otlp_span)

    # Build the ExportTraceServiceRequest
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        _kv("service.name", svc),
                    ],
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "agentguard"},
                        "spans": otlp_spans,
                    }
                ],
            }
        ]
    }


def _sec_to_nano(ts: float) -> int:
    """Convert seconds timestamp to nanoseconds."""
    return int(ts * 1_000_000_000)


def _hex_pad(val: str, length: int) -> str:
    """Ensure hex ID is padded to the OTLP expected length."""
    # Remove any dashes (from UUIDs)
    clean = val.replace("-", "")
    # Pad or truncate to expected length
    if len(clean) >= length:
        return clean[:length]
    return clean.zfill(length)


def _kv(key: str, value: Any) -> Dict[str, Any]:
    """Build an OTLP KeyValue attribute."""
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    elif isinstance(value, int):
        return {"key": key, "value": {"intValue": str(value)}}
    elif isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    else:
        return {"key": key, "value": {"stringValue": str(value)[:1000]}}
