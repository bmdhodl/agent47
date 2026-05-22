# Dogfood operator run 17 - 2026-05-22

## Goal
Keep a real AgentGuard workflow running under the SDK and leave trace-backed proof that guards enforced behavior.

## Commands run
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `agentguard demo`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed
- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` and `guard.retry_limit_exceeded` for `apply_patch` attempt 4.

## Artifacts
- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo-report.txt`
- `demo-incident.txt`
- `review-loop-incident.txt`
- `trace_inspection.txt`
- `trace_inspection.json`
- `command-output.txt`
- `pr-506-review-state.json`

## Repo health notes
- Roadmap freshness is stale at `2 weeks ago`; architecture freshness is stale at `3 weeks ago`; issue #473 tracks this.
- GitHub release/PyPI/local SDK metadata align at `1.2.10`; npm/local MCP metadata align at `0.2.2`.
- PR #506 remains the rolling proof PR for this date; GraphQL review-thread sweep found 0 unresolved threads and GitHub reports `REVIEW_REQUIRED` / `BLOCKED`.

## Verdict
Enforcement was real. The proof counted guard events from raw JSONL traces, not only CLI success output.