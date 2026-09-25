import hashlib
import io
import json
import sys

import pytest

from agentguard.demo import run_offline_demo
from agentguard.receipt import WIDTH, bars_supported, build_receipt, render


@pytest.fixture
def demo_trace(tmp_path):
    path = tmp_path / "demo.jsonl"
    assert run_offline_demo(trace_path=str(path), stream=io.StringIO()) == 0
    return path


def _write(tmp_path, events):
    path = tmp_path / "trace.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


def test_demo_receipt_lists_each_stop(demo_trace):
    receipt = build_receipt(str(demo_trace))
    assert receipt["stops"] == [
        {"kind": "budget", "detail": "$1.08 over $1.00"},
        {"kind": "loop", "detail": "search x3, same args"},
        {"kind": "retry", "detail": "fetch_docs 3 tries, limit 2"},
    ]
    assert receipt["llm_calls"] == 9
    assert receipt["recorded_cost_usd"] == 1.08
    assert receipt["sha256"] == hashlib.sha256(demo_trace.read_bytes()).hexdigest()


def test_guard_events_do_not_add_cost(tmp_path):
    # The patched client repeats the tripping call's cost on guard.budget_exceeded.
    call = {"kind": "event", "name": "llm.result", "cost_usd": 1.5, "data": {}}
    stop = {
        "kind": "event",
        "name": "guard.budget_exceeded",
        "data": {"cost_usd": 1.5, "message": "Cost budget exceeded: $6.0000 > $5.0000"},
    }
    receipt = build_receipt(str(_write(tmp_path, [call] * 4 + [stop])))
    assert receipt["recorded_cost_usd"] == 6.0
    assert receipt["stops"] == [{"kind": "budget", "detail": "Cost budget exceeded: $6.0000 > $5.0000"}]


def test_text_fits_width_and_ascii_fallback_encodes_cp1252(demo_trace):
    receipt = build_receipt(str(demo_trace))
    text = render(receipt)
    assert "STOPPED" in text
    assert all(len(line) <= WIDTH for line in text.splitlines())
    render(receipt, ascii_only=True).encode("cp1252")
    assert not bars_supported("cp1252")
    assert bars_supported("utf-8")


def test_run_without_stops_says_so(tmp_path):
    receipt = build_receipt(str(_write(tmp_path, [{"kind": "event", "name": "llm.result", "cost_usd": 0.1}])))
    assert "no guard stops" in render(receipt)


def test_markdown_and_json_formats(demo_trace):
    receipt = build_receipt(str(demo_trace))
    markdown = render(receipt, "markdown")
    assert markdown.startswith("```text\n")
    assert "not an invoice" in markdown
    assert json.loads(render(receipt, "json"))["sha256"] == receipt["sha256"]


def test_cli_receipt(demo_trace, monkeypatch, capsys):
    from agentguard import cli

    monkeypatch.setattr(sys, "argv", ["agentguard", "receipt", str(demo_trace), "--format", "json"])
    cli.main()
    assert len(json.loads(capsys.readouterr().out)["stops"]) == 3


def test_cli_receipt_empty_trace_exits(tmp_path, monkeypatch):
    from agentguard import cli

    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["agentguard", "receipt", str(empty)])
    with pytest.raises(SystemExit, match="No events"):
        cli.main()
