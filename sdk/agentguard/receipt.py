"""Plain-text run receipts from a local JSONL trace.

A receipt lists the calls AgentGuard refused, what the trace recorded, and a
SHA-256 of the trace file. The hash identifies the file; it is not a signature.
"""
from __future__ import annotations

import hashlib
import json
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List

from agentguard import __version__
from agentguard.evaluation import _extract_cost

WIDTH = 40
_BARS = "▏▎▍▌▋▊▉█"
_ASCII_BARS = "..::||II"
_KINDS = {
    "guard.budget_exceeded": "budget",
    "guard.loop_detected": "loop",
    "guard.retry_limit_exceeded": "retry",
}
_LOOP_RE = re.compile(r"repeated (\d+) times")
_RETRY_RE = re.compile(r"attempted (\d+) times \(limit: (\d+)\)")


def _stop_detail(kind: str, data: Dict[str, Any]) -> str:
    # The LangChain integration stores the reason under "error".
    message = str(data.get("message") or data.get("error") or "")
    tool = data.get("tool_name")
    if kind == "budget" and "cost_used" in data and "limit_usd" in data:
        return f"${data['cost_used']:.2f} over ${data['limit_usd']:.2f}"
    limit = data.get("calls_limit")
    if kind == "budget" and limit is not None and data.get("calls_used", 0) >= limit:
        return f"{data['calls_used']} calls, limit {limit}"
    if kind == "loop" and tool:
        match = _LOOP_RE.search(message)
        repeats = data.get("repeats") or (match and match.group(1))
        return f"{tool} x{repeats}, same args" if repeats else f"{tool} repeated"
    if kind == "retry" and tool and "failures" in data:
        return f"{tool} failed {data['failures']}x, limit {data['limit']}"
    if kind == "retry" and tool:
        match = _RETRY_RE.search(message)
        return f"{tool} {match.group(1)} tries, limit {match.group(2)}" if match else f"{tool} retried"
    return message


def build_receipt(path: str) -> Dict[str, Any]:
    """Summarize one trace file into receipt fields."""
    # One read feeds both the hash and the summary, so they describe the same bytes
    # even while a sink is still appending.
    raw = Path(path).read_bytes()
    events = []
    for line in raw.decode("utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    stops: List[Dict[str, str]] = []
    warnings = 0
    llm_calls = 0
    tool_calls = 0
    cost = 0.0
    for event in events:
        name = event.get("name")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        # Patched clients emit llm.result; the LangChain callback emits llm.end.
        if name in ("llm.result", "llm.end"):
            llm_calls += 1
        if name == "tool.call":
            tool_calls += 1
        if name == "guard.budget_warning":
            warnings += 1
        if name in _KINDS:
            stops.append({"kind": _KINDS[name], "detail": _stop_detail(_KINDS[name], data)})
        # Guard events repeat the cost of the call that tripped them.
        event_cost = None if str(name).startswith("guard.") else _extract_cost(event)
        if event_cost is not None:
            cost += event_cost
    return {
        "trace": Path(path).name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "events": len(events),
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "recorded_cost_usd": round(cost, 4),
        "budget_warnings": warnings,
        "stops": stops,
        "version": __version__,
    }


def barcode(sha256: str, width: int = WIDTH, ascii_only: bool = False) -> str:
    """Draw the hash as bars: one hex digit per column."""
    bars = _ASCII_BARS if ascii_only else _BARS
    return "".join(bars[int(digit, 16) % len(bars)] for digit in sha256[:width])


def bars_supported(encoding: str) -> bool:
    """False for encodings without block characters, such as cp1252 on Windows pipes."""
    try:
        _BARS.encode(encoding)
    except UnicodeEncodeError:
        return False
    return True


def _row(left: str, right: str) -> str:
    # Labels are short; a long value (a trace filename) keeps its end.
    if len(left) + 1 + len(right) > WIDTH:
        right = "..." + right[len(left) + 4 - WIDTH:]
    return f"{left}{' ' * (WIDTH - len(left) - len(right))}{right}"


def render_text(receipt: Dict[str, Any], ascii_only: bool = False) -> str:
    rule = "-" * WIDTH
    lines = [
        "AGENTGUARD47".center(WIDTH).rstrip(),
        "run receipt".center(WIDTH).rstrip(),
        rule,
        _row("trace", receipt["trace"]),
        _row("events", str(receipt["events"])),
    ]
    if receipt["tool_calls"]:
        lines.append(_row("tool calls", str(receipt["tool_calls"])))
    if receipt["llm_calls"] or receipt["recorded_cost_usd"]:
        lines.append(_row("llm calls", str(receipt["llm_calls"])))
        lines.append(_row("recorded cost", f"${receipt['recorded_cost_usd']:.2f}"))
    if receipt["budget_warnings"]:
        lines.append(_row("budget warnings", str(receipt["budget_warnings"])))
    lines.append(rule)
    if receipt["stops"]:
        lines.append("STOPPED")
        for stop in receipt["stops"]:
            detail = textwrap.wrap(stop["detail"], WIDTH - 10) or [""]
            lines.append(f"  {stop['kind']:<8}{detail[0]}")
            lines.extend(f"{'':10}{part}" for part in detail[1:])
    else:
        lines.append("no guard stops")
    lines += [
        rule,
        _row("guard stops", str(len(receipt["stops"]))),
        "",
        barcode(receipt["sha256"], ascii_only=ascii_only),
        " ".join(receipt["sha256"][i : i + 4] for i in range(0, 16, 4)).upper().center(WIDTH).rstrip(),
        f"sha256 of trace - agentguard47 {receipt['version']}".center(WIDTH).rstrip(),
    ]
    return "\n".join(lines)


def render(receipt: Dict[str, Any], fmt: str = "text", ascii_only: bool = False) -> str:
    if fmt == "json":
        return json.dumps(receipt)
    text = render_text(receipt, ascii_only=ascii_only)
    if fmt == "markdown":
        return f"```text\n{text}\n```\n<sub>Recorded by [AgentGuard47](https://github.com/bmdhodl/agent47). Cost is what the trace recorded, not an invoice.</sub>"
    return text
