# AgentGuard dogfood proof - 2026-05-29 run1

## Scope

SDK-only recurring dogfood run from `b0e872025e0b0980555ad5b3d376ec28f481744b`.

This run repaired the local editable install before counting installed CLI smoke output because `agentguard` initially resolved through a stale editable checkout. Repo-local proof was still bound explicitly with `PYTHONPATH=./sdk`.

## Commands

- `python -m pip install -e ./sdk`
- `agentguard doctor --trace-file doctor_trace.jsonl --json`
- `agentguard demo --trace-file demo_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file doctor_trace_repo_local.jsonl --json`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file demo_trace_repo_local.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report demo_trace_repo_local.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

## Guard behavior observed

Real enforcement was observed in raw JSONL traces.

- `demo_trace_repo_local.jsonl` emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl` emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on attempt 3.
- `coding_agent_review_loop_traces.jsonl` emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Artifacts

- `doctor_trace.jsonl`
- `doctor_trace_repo_local.jsonl`
- `demo_trace.jsonl`
- `demo_trace_repo_local.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.txt`
- `review_loop_incident.md`
- `demo_incident.json`
- `guard_events.json`
- `command_status.txt`
- `import_binding.txt`
- `staleness.log`

## Validation

- Focused proof tests: `35 passed in 1.47s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- Release health checked: GitHub release and PyPI latest are `1.2.10`; npm MCP latest is `0.2.2`; local SDK and MCP metadata match.
- Ops freshness remains stale: roadmap `3 weeks ago`, architecture `4 weeks ago`; existing tracker is #473.

## Result

Dogfood proof is healthy. No SDK code fix was needed.
