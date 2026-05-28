# Dogfood Run 21 - 2026-05-28

## Commands Run

- `agentguard doctor --trace-file installed_doctor_trace.jsonl --json`
- `agentguard demo --trace-file installed_demo_trace.jsonl`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli doctor --trace-file repo_doctor_trace.jsonl --json`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli demo --trace-file repo_demo_trace.jsonl`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli report repo_demo_trace.jsonl`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli incident repo_demo_trace.jsonl`
- `PYTHONPATH=<repo>/sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli report review_loop_trace.jsonl`
- `PYTHONPATH=<repo>/sdk python -m agentguard.cli incident review_loop_trace.jsonl`

## Guard Behavior Observed

- Installed CLI demo emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Repo-local demo emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Repo-local demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Repo-local demo emitted `guard.loop_detected` for `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls.
- Repo-local demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempted 3 times with limit 2.
- Repo-local review loop emitted `guard.budget_exceeded` on attempt 3 at `$0.0510 > $0.0450`.
- Repo-local review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Enforcement Verdict

Real enforcement observed. The demo trace contains budget, loop, and retry guard events; the coding-agent review-loop trace contains budget and retry-stop guard events from the repo-local SDK path.

## Repo Health Notes

- Roadmap freshness: 3 weeks ago.
- Architecture freshness: 4 weeks ago.
- Existing issue #473 tracks stale ops docs.
- PR #542 remains the active dogfood proof PR and is blocked by required human review.
- GitHub release, PyPI, and local SDK version are `1.2.10`; npm and local MCP package version are `0.2.2`.
- Glama still returns `tools: []`; the direct MCP Registry server endpoint returned HTTP 404 from this environment.
