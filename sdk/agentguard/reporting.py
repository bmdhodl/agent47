"""Incident-oriented reporting helpers for trace files."""
from __future__ import annotations

import html
import json
from typing import Any, Dict, List

from agentguard.evaluation import _extract_cost, _load_events, summarize_trace
from agentguard.savings import summarize_savings

_SEVERITY_ORDER = {"healthy": 0, "warning": 1, "critical": 2}


def summarize_incident(path_or_events: Any) -> Dict[str, Any]:
    """Summarize a trace with guard-focused incident metadata."""
    if isinstance(path_or_events, str):
        events = _load_events(path_or_events)
    elif isinstance(path_or_events, list):
        events = path_or_events
    else:
        raise TypeError(
            f"Expected str (file path) or list of events, got {type(path_or_events).__name__}"
        )

    summary = summarize_trace(events)
    savings = summarize_savings(events)
    summary.update(_incident_fields(events, summary))
    summary["savings"] = savings
    summary["exact_savings_usd"] = savings["exact_usd_saved"]
    return summary


def render_incident_report(
    path_or_events: Any,
    *,
    output_format: str = "markdown",
) -> str:
    """Render an incident report as markdown, html, or json."""
    incident = summarize_incident(path_or_events)
    if output_format == "json":
        return json.dumps(incident, indent=2, sort_keys=True)
    if output_format == "html":
        return _render_incident_html(incident)
    if output_format == "markdown":
        return _render_incident_markdown(incident)
    raise ValueError(
        f"output_format must be markdown, html, or json, got {output_format!r}"
    )


def _incident_fields(events: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
    guard_events: List[Dict[str, Any]] = []
    warning_count = 0
    critical_count = 0
    errors: List[Dict[str, str]] = []

    for event in events:
        name = event.get("name", "")
        error = event.get("error")
        if isinstance(error, dict):
            errors.append(
                {
                    "name": name or "(unknown)",
                    "type": str(error.get("type", "Exception")),
                    "message": str(error.get("message", "")),
                }
            )
        elif error is not None:
            errors.append(
                {
                    "name": str(name or "(unknown)"),
                    "type": type(error).__name__,
                    "message": str(error),
                }
            )
        if not isinstance(name, str) or not name.startswith("guard."):
            continue

        severity = _severity_for_event(name)
        if severity == "warning":
            warning_count += 1
        elif severity == "critical":
            critical_count += 1

        guard_events.append(
            {
                "name": name,
                "severity": severity,
                "message": _event_message(event),
                "cost_usd": _extract_cost(event),
            }
        )

    severity = "healthy"
    if critical_count or errors:
        severity = "critical"
    elif warning_count:
        severity = "warning"

    primary_cause = _primary_cause(guard_events, errors)
    estimated_savings = _estimate_savings(summary["cost_usd"], guard_events, errors)

    return {
        "severity": severity,
        "status": "incident" if severity != "healthy" else "ok",
        "primary_cause": primary_cause,
        "guard_event_count": len(guard_events),
        "guard_events": guard_events,
        "warning_count": warning_count,
        "critical_count": critical_count,
        "error_details": errors,
        "estimated_savings_usd": estimated_savings,
        "recommendations": _recommendations(primary_cause, severity),
    }


def _severity_for_event(name: str) -> str:
    if name.endswith("warning"):
        return "warning"
    return "critical"


def _event_message(event: Dict[str, Any]) -> str:
    data = event.get("data")
    if isinstance(data, dict):
        message = data.get("message")
        if message:
            return str(message)
    error = event.get("error")
    if isinstance(error, dict):
        return str(error.get("message", ""))
    return ""


def _primary_cause(guard_events: List[Dict[str, Any]], errors: List[Dict[str, str]]) -> str:
    if any(e["name"] == "guard.loop_detected" for e in guard_events):
        return "loop_detected"
    if any(e["name"] == "guard.retry_limit_exceeded" for e in guard_events):
        return "retry_limit_exceeded"
    if any(e["name"] == "guard.budget_exceeded" for e in guard_events):
        return "budget_exceeded"
    if any(e["name"] == "guard.budget_warning" for e in guard_events):
        return "budget_warning"
    if errors:
        return "error"
    return "healthy"


def _estimate_savings(
    total_cost: float,
    guard_events: List[Dict[str, Any]],
    errors: List[Dict[str, str]],
) -> float:
    """Conservative savings proxy: one more comparable failing cycle avoided."""
    if any(e["name"] in {"guard.loop_detected", "guard.budget_exceeded"} for e in guard_events):
        return round(total_cost, 4)
    if errors and total_cost > 0:
        return round(total_cost * 0.5, 4)
    return 0.0


def _recommendations(primary_cause: str, severity: str) -> List[str]:
    base = [
        "Review the trace timeline to confirm the failure path before widening limits.",
        (
            "Keep one-off investigations local; add HttpSink only when future incidents "
            "need retained history, alerts, or team-visible follow-up."
        ),
    ]
    if primary_cause == "loop_detected":
        return [
            "Tighten LoopGuard or FuzzyLoopGuard thresholds around the repeated tool path.",
            "Add a cheaper fallback or deterministic exit when the same tool repeats.",
            *base,
        ]
    if primary_cause == "budget_exceeded":
        return [
            "Lower per-run budget or switch the hot path to a cheaper model.",
            "Add CI cost gates so regressions fail before production traffic hits them.",
            *base,
        ]
    if primary_cause == "retry_limit_exceeded":
        return [
            "Add exponential backoff or a deterministic fallback before retrying the same tool.",
            "Treat repeated upstream failures as a stop condition instead of widening the retry ceiling.",
            *base,
        ]
    if primary_cause == "budget_warning":
        return [
            "Treat this trace as an early warning and inspect the highest-cost span first.",
            "Add a hard budget if you are still warning-only in production.",
            *base,
        ]
    if severity == "critical":
        return [
            "Inspect the failing span and error payload before retrying this workflow.",
            *base,
        ]
    return [
        "Keep this trace as a baseline and add CI assertions to hold the budget line.",
        *base,
    ]


def _render_incident_markdown(incident: Dict[str, Any]) -> str:
    lines = [
        "# AgentGuard Incident Report",
        "",
        f"Status: **{incident['status']}**",
        f"Severity: **{incident['severity']}**",
        f"Primary cause: **{incident['primary_cause']}**",
        "",
        "## Summary",
        "",
        f"- Total events: {incident['total_events']}",
        f"- Spans: {incident['spans']}",
        f"- Events: {incident['events']}",
        f"- Duration: {incident['duration_ms']:.1f} ms",
        f"- Estimated cost: ${incident['cost_usd']:.4f}",
        f"- Guard events: {incident['guard_event_count']}",
        f"- Errors: {incident['errors']}",
        f"- Exact savings: ${incident['savings']['exact_usd_saved']:.4f}",
        f"- Estimated savings: ${incident['savings']['estimated_usd_saved']:.4f}",
        "",
    ]
    lines.extend(
        [
            "## Savings Ledger",
            "",
            f"- Exact tokens saved: {incident['savings']['exact_tokens_saved']}",
            f"- Estimated tokens saved: {incident['savings']['estimated_tokens_saved']}",
            f"- Exact dollars saved: ${incident['savings']['exact_usd_saved']:.4f}",
            f"- Estimated dollars saved: ${incident['savings']['estimated_usd_saved']:.4f}",
        ]
    )
    if incident["savings"]["reasons"]:
        lines.append("- Savings reasons:")
        for reason in incident["savings"]["reasons"]:
            lines.append(
                "  - "
                f"`{reason['kind']}` ({reason['confidence']}): "
                f"{reason['tokens_saved']} tokens / ${reason['usd_saved']:.4f} "
                f"across {reason['occurrences']} occurrence(s)"
            )
    lines.append("")
    if incident["guard_events"]:
        lines.extend(["## Guard Events", ""])
        for event in incident["guard_events"]:
            detail = f": {event['message']}" if event["message"] else ""
            lines.append(f"- `{event['name']}` ({event['severity']}){detail}")
        lines.append("")
    if incident["error_details"]:
        lines.extend(["## Errors", ""])
        for error in incident["error_details"]:
            lines.append(
                f"- `{error['name']}` `{error['type']}`: {error['message']}"
            )
        lines.append("")
    lines.extend(["## Recommended Next Steps", ""])
    for item in incident["recommendations"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Upgrade Path",
            "",
            (
                "Keep this report local if it is a one-off investigation. Add hosted ingest "
                "only when future incidents need retained history, alerts, spend trends, or "
                "team-visible follow-up:"
            ),
            "",
            "```python",
            "from agentguard import Tracer, HttpSink",
            "",
            'tracer = Tracer(sink=HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_..."))',
            "```",
        ]
    )
    return "\n".join(lines)


def _render_incident_html(incident: Dict[str, Any]) -> str:
    guard_items = "".join(
        (
            "<li><code>{name}</code> ({severity}){detail}</li>".format(
                name=html.escape(event["name"]),
                severity=html.escape(event["severity"]),
                detail=(
                    ": " + html.escape(event["message"])
                    if event["message"]
                    else ""
                ),
            )
        )
        for event in incident["guard_events"]
    ) or "<li>No guard events recorded.</li>"
    rec_items = "".join(
        f"<li>{html.escape(item)}</li>" for item in incident["recommendations"]
    )
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>AgentGuard Incident Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 32px; color: #1e1b16; }}
      .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
      code {{ background: #f6f6f6; padding: 2px 4px; }}
      pre {{ background: #111827; color: #f9fafb; padding: 16px; border-radius: 10px; overflow-x: auto; }}
    </style>
  </head>
  <body>
    <h1>AgentGuard Incident Report</h1>
    <div class="card">
      <p><strong>Status:</strong> {status}</p>
      <p><strong>Severity:</strong> {severity}</p>
      <p><strong>Primary cause:</strong> {primary_cause}</p>
      <p><strong>Estimated cost:</strong> ${cost:.4f}</p>
      <p><strong>Exact savings:</strong> ${exact_savings:.4f}</p>
      <p><strong>Estimated savings:</strong> ${estimated_savings:.4f}</p>
    </div>
    <div class="card">
      <h2>Savings Ledger</h2>
      <p><strong>Exact tokens saved:</strong> {exact_tokens}</p>
      <p><strong>Estimated tokens saved:</strong> {estimated_tokens}</p>
      <ul>{savings_items}</ul>
    </div>
    <div class="card">
      <h2>Guard Events</h2>
      <ul>{guard_items}</ul>
    </div>
    <div class="card">
      <h2>Recommended Next Steps</h2>
      <ul>{rec_items}</ul>
    </div>
    <div class="card">
      <h2>Upgrade Path</h2>
      <p>Keep this report local if it is a one-off investigation. Add hosted ingest only when future incidents need retained history, alerts, spend trends, or team-visible follow-up.</p>
      <pre>from agentguard import Tracer, HttpSink

tracer = Tracer(sink=HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_..."))</pre>
    </div>
  </body>
</html>
""".format(
        status=html.escape(incident["status"]),
        severity=html.escape(incident["severity"]),
        primary_cause=html.escape(incident["primary_cause"]),
        cost=incident["cost_usd"],
        exact_savings=incident["savings"]["exact_usd_saved"],
        estimated_savings=incident["savings"]["estimated_usd_saved"],
        exact_tokens=incident["savings"]["exact_tokens_saved"],
        estimated_tokens=incident["savings"]["estimated_tokens_saved"],
        savings_items=(
            "".join(
                f"<li><code>{html.escape(reason['kind'])}</code> "
                f"({html.escape(reason['confidence'])}): "
                f"{reason['tokens_saved']} tokens / ${reason['usd_saved']:.4f} "
                f"across {reason['occurrences']} occurrence(s)</li>"
                for reason in incident["savings"]["reasons"]
            )
            or "<li>No savings signals detected.</li>"
        ),
        guard_items=guard_items,
        rec_items=rec_items,
    )
