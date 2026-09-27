"""Offline tests for scripts/live_cost_reconcile.py against recorded, scrubbed responses."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "live_cost_reconcile.py"
SPEC = importlib.util.spec_from_file_location("live_cost_reconcile", SCRIPT_PATH)
assert SPEC is not None
rec = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = rec
SPEC.loader.exec_module(rec)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "live_cost"
TRACE = (FIXTURES / "trace.jsonl").read_text(encoding="utf-8").splitlines()
RESPONSES = json.loads((FIXTURES / "admin-responses.json").read_text(encoding="utf-8"))


def replay(path: str, bucket_width: str):
    """Getter that serves the last recorded response for (path, bucket_width, page)."""
    recorded = {}
    for r in RESPONSES:
        if r["path"] == path and r["params"]["bucket_width"] == bucket_width:
            recorded[r["params"].get("page")] = r["body"]
    calls = []

    def get(p, params):
        calls.append(dict(params))
        return recorded[params.get("page")]

    return get, calls


def test_recorded_totals_group_by_alias_and_sum_cost():
    totals, costs = rec.recorded_totals(TRACE)
    assert totals == {
        "gpt-4.1-nano": {"requests": 3, "input": 4119, "cached": 1920, "output": 5},
        "gpt-4o-mini": {"requests": 2, "input": 26, "cached": 0, "output": 6},
        "gpt-5-nano": {"requests": 1, "input": 12, "cached": 0, "output": 19},
    }
    assert abs(costs["gpt-4.1-nano"] - (1.7e-06 + 2.061e-04 + 6.21e-05)) < 1e-15


def test_recorded_run_matches_openai_usage():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    assert rec.covered(totals, openai)
    ok, lines = rec.compare(totals, costs, openai)
    assert ok, "\n".join(lines)
    assert len(lines) == 1 + 3 * 5
    assert all(line.endswith("ok") for line in lines[1:])


def test_token_mismatch_fails_gate_with_diff_line():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    openai["gpt-4.1-nano"]["cached"] -= 1
    ok, lines = rec.compare(totals, costs, openai)
    assert not ok
    bad = [line for line in lines if "MISMATCH" in line]
    # One cached token moves both the token row and the cost row.
    assert [line.split()[:2] for line in bad] == [["gpt-4.1-nano", "cached"], ["gpt-4.1-nano", "cost_usd"]]


def test_cost_drift_beyond_tolerance_fails_gate():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    costs["gpt-5-nano"] += 2e-9
    ok, lines = rec.compare(totals, costs, openai)
    assert not ok
    assert [line.split()[:2] for line in lines if "MISMATCH" in line] == [["gpt-5-nano", "cost_usd"]]


def test_same_model_traffic_in_window_fails_gate_without_publishing_org_totals():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    openai["gpt-4o-mini"] = {"requests": 7, "input": 9000, "cached": 0, "output": 400}
    ok, lines = rec.compare(totals, costs, openai)
    assert not ok
    mini = [line for line in lines if line.startswith("gpt-4o-mini")]
    assert mini[0].split() == ["gpt-4o-mini", "requests", "2", ">2", "MISMATCH"]
    assert mini[-1].split()[-2:] == ["redacted", "MISMATCH"]
    assert not any(n in line.split() for line in mini for n in ("7", "9000", "400"))


def test_miscount_with_equal_requests_shows_openai_values():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    openai["gpt-5-nano"]["output"] += 3
    ok, lines = rec.compare(totals, costs, openai)
    assert not ok
    assert ["gpt-5-nano", "output", "19", "22", "MISMATCH"] in [line.split() for line in lines]


def test_models_only_openai_saw_are_listed_not_gated():
    get, _ = replay("usage/completions", "1m")
    openai = rec.usage_totals(get, 0, 60)
    totals, costs = rec.recorded_totals(TRACE)
    openai["gpt-unlisted-9"] = {"requests": 2, "input": 5, "cached": 0, "output": 1}
    ok, lines = rec.compare(totals, costs, openai)
    assert ok, "\n".join(lines)
    assert lines[-1] == "other traffic in window on 1 model(s), not gated"
    assert "gpt-unlisted-9" not in "\n".join(lines)


def test_unpriced_recorded_model_fails_gate_without_crashing():
    usage = {"requests": 1, "input": 5, "cached": 0, "output": 1}
    ok, lines = rec.compare({"gpt-unlisted-9": dict(usage)}, {"gpt-unlisted-9": 0.001},
                            {"gpt-unlisted-9": dict(usage)})
    assert not ok
    assert "nan" in lines[-1] and lines[-1].endswith("MISMATCH")


def test_not_covered_until_every_request_lands():
    totals, _ = rec.recorded_totals(TRACE)
    partial = {m: dict(t) for m, t in totals.items()}
    partial["gpt-4o-mini"]["requests"] -= 1
    assert not rec.covered(totals, partial)
    del partial["gpt-5-nano"]
    assert not rec.covered(totals, partial)
    assert rec.covered(totals, totals)


def test_pagination_follows_next_page_and_sums_every_bucket():
    row = {"model": "gpt-5-nano-2025-08-07", "num_model_requests": 1, "input_tokens": 10,
           "input_cached_tokens": 0, "output_tokens": 3}
    pages = {
        None: {"data": [{"results": [row]}, {"results": []}], "has_more": True, "next_page": "p2"},
        "p2": {"data": [{"results": [row, dict(row, model="gpt-4o-mini-2024-07-18")]}],
               "has_more": False, "next_page": None},
    }
    seen = []

    def get(path, params):
        seen.append((path, params.get("page"), params["group_by"], params["bucket_width"]))
        return pages[params.get("page")]

    totals = rec.usage_totals(get, 0, 120)
    assert seen == [("usage/completions", None, ["model"], "1m"), ("usage/completions", "p2", ["model"], "1m")]
    assert totals["gpt-5-nano"] == {"requests": 2, "input": 20, "cached": 0, "output": 6}
    assert totals["gpt-4o-mini"]["requests"] == 1


def test_null_results_and_empty_window():
    def get(path, params):
        return {"data": [{"results": []}], "has_more": False, "next_page": None}

    assert rec.usage_totals(get, 0, 60) == {}
    ok, lines = rec.compare({}, {}, {})
    assert ok and len(lines) == 1


def test_cost_report_prints_ratio_per_model_and_total():
    usage_get, _ = replay("usage/completions", "1d")
    costs_get, _ = replay("costs", "1d")

    def get(path, params):
        return (costs_get if path == "costs" else usage_get)(path, params)

    lines = rec.cost_report(get, datetime(2026, 9, 25, tzinfo=timezone.utc))
    assert lines[0].startswith("Costs API vs usage x price table, 2026-09-25 UTC")
    assert lines[-1].startswith("TOTAL")
    assert len(lines[-1].split()) == 2


def test_cost_report_handles_unpriced_line_items():
    def get(path, params):
        if path == "costs":
            results = [{"line_item": "web search tool calls", "amount": {"value": 0.01}},
                       {"line_item": None, "amount": {"value": 0.0}}]
        else:
            results = []
        return {"data": [{"results": results}], "has_more": False}

    lines = rec.cost_report(get, datetime(2026, 9, 25, tzinfo=timezone.utc))
    assert "n/a" in lines[-1]
    # Org-wide dollars never reach the public log.
    assert not any(re.search(r"\d\.\d{6}", line) for line in lines)


def test_base_model_strips_snapshot_date_only():
    assert rec.base_model("gpt-4o-mini-2024-07-18") == "gpt-4o-mini"
    assert rec.base_model("gpt-5-nano") == "gpt-5-nano"
    assert rec.base_model("gpt-4.1-nano-2025-04-14") == "gpt-4.1-nano"
    # A snapshot with its own, higher price row keeps its id.
    assert rec.base_model("gpt-4o-2024-05-13") == "gpt-4o-2024-05-13"
    assert rec.table_cost("gpt-4o-2024-05-13", {"input": 1_000_000, "cached": 0, "output": 0}) == 5.0


def test_scrub_drops_identifiers():
    body = {"data": [{"results": [{"project_id": "p", "api_key_id": "k", "organization_id": "o",
                                   "user_id": "u", "model": "gpt-5-nano"}]}]}
    row = rec.scrub(body)["data"][0]["results"][0]
    assert row == {"project_id": None, "api_key_id": None, "organization_id": None,
                   "user_id": None, "model": "gpt-5-nano"}


def test_fixtures_carry_no_org_project_or_key_ids():
    text = (FIXTURES / "admin-responses.json").read_text(encoding="utf-8")
    text += "\n".join(TRACE)
    assert not re.search(r"\b(org|proj|key|user)[-_][A-Za-z0-9]{6,}|sk-[A-Za-z0-9]", text)
