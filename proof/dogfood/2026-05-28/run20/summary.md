# Dogfood Run 20 - 2026-05-28

## Commands Run

- `agentguard doctor` (installed CLI smoke)
- `agentguard demo` (installed CLI smoke)
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli doctor`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli demo`
- `PYTHONPATH=<repo>/sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli report ... --json` for demo and review-loop traces
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli incident ...` for review-loop markdown and JSON output

## Guard Behavior Observed

- Installed CLI smoke produced the same demo guard events as the repo-local run: `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Repo-local demo emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Repo-local demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Repo-local demo emitted `guard.loop_detected` for `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls.
- Repo-local demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempted 3 times with limit 2.
- Repo-local review-loop emitted `guard.budget_exceeded` on attempt 3 at `$0.0510 > $0.0450`.
- Repo-local review-loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Enforcement Verdict

Real enforcement observed. The demo trace contains budget, loop, and retry guard events; the coding-agent review loop contains budget and retry-stop guard events from the repo-local SDK import path.

## Repo Health Notes

- Roadmap freshness: 3 weeks ago.
- Architecture freshness: 4 weeks ago.
- Existing issue #473 tracks the stale ops docs.
- PR #542 remains the active dogfood proof PR and is blocked by required human review.
