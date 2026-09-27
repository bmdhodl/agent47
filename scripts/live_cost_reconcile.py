"""Reconcile AgentGuard's recorded OpenAI costs against OpenAI's own usage records.

Makes a tiny fixed set of real calls through the patched OpenAI client, reads
what AgentGuard recorded from the JSONL trace, then polls the organization
Usage API until OpenAI's counts for the run window cover every call.

Gate (exit 1 on failure):
  * per model: requests, input, cached-input and output tokens match exactly;
  * cost from OpenAI's token counts x the price table equals AgentGuard's
    recorded cost within 1e-9.
Report only: the D-2 Costs API total against D-2 usage x the price table.

Needs OPENAI_API_KEY (model calls) and OPENAI_ADMIN_KEY (/v1/organization/*).
Spend per run is well under $0.01; a BudgetGuard caps it at $0.02.

Isolation: the Usage API window is the run's own minutes, grouped by model.
Other traffic on the same models inside those minutes shows up as OpenAI > AgentGuard.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agentguard.price_table import get_default_prices, lookup_rate

API = "https://api.openai.com/v1/organization/"
FIELDS = ("requests", "input", "cached", "output")
COST_TOLERANCE = 1e-9
_DATED = re.compile(r"-\d{4}-\d{2}-\d{2}$")
_SCRUB_KEYS = ("project_id", "api_key_id", "user_id", "organization_id",
               "organization_name", "project_name")

Getter = Callable[[str, Mapping[str, Any]], dict[str, Any]]
Totals = dict[str, dict[str, int]]


def base_model(model: str) -> str:
    """OpenAI reports the dated snapshot (gpt-4o-mini-2024-07-18); key by the alias."""
    return _DATED.sub("", model)


def recorded_totals(trace_lines: list[str]) -> tuple[Totals, dict[str, float]]:
    """Per-model token totals and recorded cost from AgentGuard's llm.result events."""
    totals: Totals = {}
    costs: dict[str, float] = {}
    for line in trace_lines:
        event = json.loads(line)
        if event.get("name") != "llm.result":
            continue
        data = event["data"]
        usage = data["usage"]
        model = base_model(data["model"])
        row = totals.setdefault(model, dict.fromkeys(FIELDS, 0))
        row["requests"] += 1
        row["input"] += usage["input_tokens"]
        row["cached"] += usage.get("cached_input_tokens", 0)
        row["output"] += usage["output_tokens"]
        costs[model] = costs.get(model, 0.0) + event["cost_usd"]
    return totals, costs


def paged(get: Getter, path: str, params: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    """Every result row across all buckets and pages."""
    query = dict(params)
    while True:
        body = get(path, query)
        for bucket in body["data"]:
            yield from bucket["results"]
        if not body.get("has_more"):
            return
        query["page"] = body["next_page"]


def usage_totals(get: Getter, start: int, end: int, bucket_width: str = "1m") -> Totals:
    """Per-model totals from GET /organization/usage/completions over [start, end)."""
    params = {"start_time": start, "end_time": end, "bucket_width": bucket_width,
              "group_by": ["model"], "limit": 1440 if bucket_width == "1m" else 31}
    totals: Totals = {}
    for r in paged(get, "usage/completions", params):
        row = totals.setdefault(base_model(r["model"]), dict.fromkeys(FIELDS, 0))
        row["requests"] += r["num_model_requests"]
        row["input"] += r["input_tokens"]
        row["cached"] += r["input_cached_tokens"]
        row["output"] += r["output_tokens"]
    return totals


def table_cost(model: str, t: Mapping[str, int]) -> float:
    """Standard-tier cost of these token counts from AgentGuard's price table."""
    rate = lookup_rate(get_default_prices(), "openai", model)
    if rate is None:
        raise KeyError(f"no OpenAI price row for {model}")
    cached_rate = rate.get("cached_input_per_1m", rate["input_per_1m"])
    return ((t["input"] - t["cached"]) * rate["input_per_1m"]
            + t["cached"] * cached_rate
            + t["output"] * rate["output_per_1m"]) / 1_000_000


def covered(recorded: Totals, openai: Totals) -> bool:
    """OpenAI has counted at least as many requests as AgentGuard made, per model."""
    return all(openai.get(m, {}).get("requests", 0) >= r["requests"] for m, r in recorded.items())


def compare(recorded: Totals, recorded_cost: Mapping[str, float], openai: Totals) -> tuple[bool, list[str]]:
    """Gate result and a diff table (one line per model and field)."""
    lines = [f"{'model':16} {'field':9} {'agentguard':>14} {'openai':>14}  result"]
    ok = True
    for model in sorted(set(recorded) | set(openai)):
        ours = recorded.get(model, dict.fromkeys(FIELDS, 0))
        theirs = openai.get(model, dict.fromkeys(FIELDS, 0))
        for field in FIELDS:
            match = ours[field] == theirs[field]
            ok &= match
            lines.append(f"{model:16} {field:9} {ours[field]:>14} {theirs[field]:>14}  "
                         f"{'ok' if match else 'MISMATCH'}")
        expected = table_cost(model, theirs)
        got = recorded_cost.get(model, 0.0)
        match = abs(got - expected) <= COST_TOLERANCE
        ok &= match
        lines.append(f"{model:16} {'cost_usd':9} {got:>14.10f} {expected:>14.10f}  "
                     f"{'ok' if match else 'MISMATCH'}")
    return ok, lines


def cost_report(get: Getter, day: datetime) -> list[str]:
    """Report-only: billed cost for one UTC day vs that day's usage x the price table."""
    start = int(day.timestamp())
    end = start + 86400
    billed: dict[str, float] = {}
    for r in paged(get, "costs", {"start_time": start, "end_time": end, "bucket_width": "1d",
                                  "group_by": ["line_item"], "limit": 1}):
        model = base_model((r.get("line_item") or "unattributed").split(", ")[0])
        billed[model] = billed.get(model, 0.0) + float(r["amount"]["value"])
    usage = usage_totals(get, start, end, bucket_width="1d")
    lines = [f"Costs API vs usage x price table, {day.date()} UTC (report only; costs lag and round)",
             f"{'model':24} {'billed':>12} {'table':>12} {'ratio':>8}"]
    total_billed = total_table = 0.0
    for model in sorted(set(billed) | set(usage)):
        if model in usage and lookup_rate(get_default_prices(), "openai", model) is not None:
            table = table_cost(model, usage[model])
        else:
            table = 0.0
        paid = billed.get(model, 0.0)
        total_billed += paid
        total_table += table
        ratio = f"{paid / table:.4f}" if table else "n/a"
        lines.append(f"{model:24} {paid:>12.6f} {table:>12.6f} {ratio:>8}")
    ratio = f"{total_billed / total_table:.4f}" if total_table else "n/a"
    lines.append(f"{'TOTAL':24} {total_billed:>12.6f} {total_table:>12.6f} {ratio:>8}")
    return lines


def scrub(body: Any) -> Any:
    """Drop org, project, key and user identifiers from an admin API response."""
    if isinstance(body, dict):
        return {k: (None if k in _SCRUB_KEYS else scrub(v)) for k, v in body.items()}
    if isinstance(body, list):
        return [scrub(v) for v in body]
    return body


def admin_getter(admin_key: str, raw: list[dict[str, Any]]) -> Getter:
    def get(path: str, params: Mapping[str, Any]) -> dict[str, Any]:
        url = API + path + "?" + urllib.parse.urlencode(params, doseq=True)
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {admin_key}"})
        with urllib.request.urlopen(request, timeout=60) as response:  # nosec B310 - fixed https host
            body = json.load(response)
        raw.append({"path": path, "params": dict(params), "body": scrub(body)})
        return body
    return get


LONG_PROMPT = "\n".join(
    f"Ledger line {i:03d}: agent run {i} stopped after a recorded budget check passed."
    for i in range(1, 121)
) + "\nReply with the word ok."


def run_calls(trace_path: Path) -> tuple[float, float, float]:
    """The fixed call set. Returns (run start, run end, guard cost)."""
    from agentguard import BudgetGuard, JsonlFileSink, Tracer
    from agentguard.instrument import patch_openai

    guard = BudgetGuard(max_cost_usd=0.02)
    tracer = Tracer(sink=JsonlFileSink(str(trace_path)), service="live-cost-reconcile", watermark=False)
    patch_openai(tracer, budget_guard=guard)
    import openai

    client = openai.OpenAI()
    start = time.time()
    client.chat.completions.create(model="gpt-4.1-nano", max_tokens=5,
                                   messages=[{"role": "user", "content": "Reply with the word ok."}])
    client.responses.create(model="gpt-4o-mini", input="Reply with the word ok.", max_output_tokens=16)
    with client.responses.create(model="gpt-4o-mini", input="Reply with the word ok.",
                                 max_output_tokens=16, stream=True) as stream:
        for _ in stream:
            pass
    client.responses.create(model="gpt-5-nano", input="Reply with the word ok.",
                            reasoning={"effort": "minimal"}, max_output_tokens=64)
    for _ in range(2):  # the second send reads the first from the prompt cache
        client.responses.create(model="gpt-4.1-nano", input=LONG_PROMPT, max_output_tokens=16,
                                prompt_cache_key="agentguard-live-cost-reconcile")
    return start, time.time(), guard.state.cost_used


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path(".pytest_cache/live-cost-reconcile"),
                        help="directory for trace.jsonl, report.txt and scrubbed admin responses")
    parser.add_argument("--timeout", type=int, default=900, help="seconds to wait for usage to land")
    parser.add_argument("--poll", type=int, default=30, help="seconds between usage polls")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    trace_path = args.out / "trace.jsonl"
    trace_path.unlink(missing_ok=True)
    report: list[str] = []

    def say(line: str = "") -> None:
        print(line, flush=True)
        report.append(line)

    run_start, run_end, guard_cost = run_calls(trace_path)
    recorded, recorded_cost = recorded_totals(trace_path.read_text(encoding="utf-8").splitlines())
    window = (int(run_start) // 60 * 60, (int(run_end) // 60 + 2) * 60)
    say(f"calls {sum(r['requests'] for r in recorded.values())} | guard cost ${guard_cost:.8f} | "
        f"window {datetime.fromtimestamp(window[0], timezone.utc):%Y-%m-%dT%H:%MZ} +"
        f"{(window[1] - window[0]) // 60}m")

    raw: list[dict[str, Any]] = []
    get = admin_getter(os.environ["OPENAI_ADMIN_KEY"], raw)
    deadline = time.monotonic() + args.timeout
    previous = None
    while True:
        openai_totals = usage_totals(get, *window)
        # Usage lands in pieces; accept it once it covers every call and holds for one poll.
        if covered(recorded, openai_totals) and openai_totals == previous:
            break
        if time.monotonic() > deadline:
            say(f"TIMEOUT after {args.timeout}s: OpenAI usage never covered every call")
            break
        previous = openai_totals if covered(recorded, openai_totals) else None
        time.sleep(args.poll)

    ok, diff = compare(recorded, recorded_cost, openai_totals)
    say()
    for line in diff:
        say(line)
    say()
    say("GATE PASS" if ok else "GATE FAIL: AgentGuard's record does not match OpenAI's")

    say()
    day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
    for line in cost_report(get, day):
        say(line)

    (args.out / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (args.out / "admin-responses.json").write_text(json.dumps(raw, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
