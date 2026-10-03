"""Elapsed duration across sibling spans and the existing report consumers."""
from __future__ import annotations

import json

import pytest

from agentguard import EvalSuite, summarize_trace
from agentguard.cli import _report
from agentguard.reporting import render_incident_report


def _span(name, start, end):
    return [
        {"kind": "span", "phase": "start", "name": name, "ts": start},
        {"kind": "span", "phase": "end", "name": name, "ts": end,
         "duration_ms": (end - start) * 1000},
    ]


_SEQUENTIAL = _span("call.one", 0, .153) + _span("call.two", .1532, .3019) + _span("call.three", .3021, .4466)
_OVERLAP = _span("call.one", 1, 1.4) + _span("call.two", 1.1, 1.3) + _span("call.three", 1.2, 1.5)
_NESTED = _span("agent.run", 0, 3) + _span("call.one", .2, 1) + _span("call.two", 1.1, 2)
_LEGACY = [{"kind": "span", "phase": "end", "name": "call", "duration_ms": value} for value in (100, 500)]
_INVALID = [*_span("call", 1, 1.4),
    {"kind": "span", "phase": "start", "name": "invalid", "ts": False},
    {"kind": "span", "phase": "start", "name": "invalid", "ts": "-100"},
    {"kind": "span", "phase": "start", "name": "invalid", "ts": float("nan")},
    {"kind": "span", "phase": "end", "name": "invalid", "ts": float("inf"), "duration_ms": float("inf")},
]


@pytest.mark.parametrize("consumer", ["summary", "report", "incident"])
@pytest.mark.parametrize("events, expected_ms", [
    pytest.param(_SEQUENTIAL, 446.6, id="sequential-no-root"),
    pytest.param(_OVERLAP, 500, id="overlapping-no-double-count"),
    pytest.param(_NESTED, 3000, id="nested-root"),
    pytest.param(list(reversed(_SEQUENTIAL)), 446.6, id="unordered-file"),
    pytest.param([dict(event, duration_ms=None) for event in _span("call", 1, 3.5)], 2500, id="timestamps-only"),
    pytest.param(_LEGACY, 500, id="legacy-duration-only"),
    pytest.param([dict(event, ts=10) for event in _LEGACY], 500, id="end-only"),
    pytest.param([*_SEQUENTIAL, {"kind": "event", "phase": "emit", "name": "note", "ts": 500}], 446.6, id="ignore-point-events"),
    pytest.param([{"kind": "span", "phase": "start", "name": "call", "ts": 5}, {"kind": "span", "phase": "end", "name": "call", "ts": 4, "duration_ms": 250}], 250, id="backward-clock-fallback"),
    pytest.param(_INVALID, 400, id="invalid-nonfinite-timing"),
    pytest.param([{"kind": "span", "phase": "start", "name": "call", "ts": 1}], None, id="incomplete-no-duration"),
])
def test_elapsed_duration_consumers(events, expected_ms, consumer, tmp_path, capsys):
    """REGRESSION: reports must show the elapsed span timeline, not its slowest call."""
    path = tmp_path / "trace.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    if consumer == "summary":
        assert summarize_trace(str(path))["duration_ms"] == pytest.approx(expected_ms or 0)
    elif consumer == "report":
        _report(str(path), as_json=True)
        report = json.loads(capsys.readouterr().out)
        if expected_ms is None:
            assert report["approx_run_time_ms"] is None
        else:
            assert report["approx_run_time_ms"] == pytest.approx(expected_ms)
        _report(str(path))
        text = capsys.readouterr().out
        if expected_ms is None:
            assert "Approx run time" not in text
        else:
            assert f"Approx run time: {expected_ms:.1f} ms" in text
    else:
        incident = json.loads(render_incident_report(str(path), output_format="json"))
        assert incident["duration_ms"] == pytest.approx(expected_ms or 0)
        assert f"Duration: {(expected_ms or 0):.1f} ms" in render_incident_report(str(path))


def test_elapsed_summary_preserves_longest_span_assertion(tmp_path):
    path = tmp_path / "trace.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in _SEQUENTIAL), encoding="utf-8")
    # This assertion explicitly tests the longest span, independently of report timing.
    assert EvalSuite(str(path)).assert_completes_within(.2).run().passed


def test_empty_duration_summary():
    assert summarize_trace([])["duration_ms"] == 0
