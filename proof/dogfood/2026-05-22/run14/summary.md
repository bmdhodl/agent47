# Dogfood proof - 2026-05-22 run 14

## Scope

SDK-only dogfood run from the active AgentGuard checkout. No dashboard,
auth, billing, secrets, deployments, paid-feature code, or release work.

## Commands run

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

The proof is trace-backed. It is not just command success.

### Offline demo trace

Raw trace: `agentguard_demo_traces.jsonl`

- `guard.budget_warning` emitted at `$0.8400 / $1.0000`
- `guard.budget_exceeded` stopped spend at `$1.0800 > $1.0000`
- `guard.loop_detected` stopped repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded` stopped `fetch_docs` after attempt 3 with limit 2

### Coding-agent review loop trace

Raw trace: `coding_agent_review_loop_traces.jsonl`

- `guard.budget_exceeded` stopped the review loop on attempt 3 at
  `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded` stopped `apply_patch` on attempt 4 with limit 3

## Artifact files

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard-doctor-output.txt`
- `python-doctor-output.txt`
- `demo-output.txt`
- `review-loop-output.txt`
- `demo-report.txt`
- `review-loop-incident.txt`
- `trace-inspection.txt`

## Validation

- Focused proof/metadata tests: `35 passed in 1.57s`
- MCP npm release guard: `Release guard passed.`
- Artifact encoding/local-path scan: clean after normalization

## Repo health notes

- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old.
- `ops/02-ARCHITECTURE.md` is 3 weeks old.
- Existing issue `#473` still tracks the stale ops-doc cadence.
- Latest GitHub release is `v1.2.10`; PyPI latest is `1.2.10`.
- Local SDK metadata is `1.2.10`.
- npm `@agentguard47/mcp-server` and local MCP metadata are `0.2.2`.
- Official MCP Registry metadata remains stale at `0.2.1`.
- Glama remains the distribution follow-up until the seven MCP tools index.

## Notes

The review-loop incident report on this branch still reports estimated cost as
`$0.1020` even though the enforcing guard event stopped at `$0.0510`. This is a
known proof-reporting drift already fixed in PR `#502`, so this proof-only run
does not duplicate that code change.
