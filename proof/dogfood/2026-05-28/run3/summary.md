# AgentGuard Dogfood Run 3 - 2026-05-28

## Scope

- SDK-only dogfood run from branch `dogfood-2026-05-28-run3-worker`.
- No dashboard, auth, billing, secrets, deployment, paid-feature, or release work.
- Roadmap and architecture docs are stale by the repo thresholds: roadmap `3 weeks ago`, architecture `4 weeks ago`.

## Commands Run

- `where.exe agentguard`
- `agentguard doctor --trace-file proof/dogfood/2026-05-28/run3/installed_agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-28/run3/installed_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run3/repo_agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run3/repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-28/run3/repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-28/run3/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `PYTHONPATH=./sdk python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard Behavior Observed

Trace inspection found 10 concrete guard events:

- Installed demo trace: `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, `guard.retry_limit_exceeded`.
- Repo-local demo trace: `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, `guard.retry_limit_exceeded`.
- Repo-local review-loop trace: `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- Repo-local review-loop trace: `guard.retry_limit_exceeded` on `apply_patch` attempt 4 with limit 3.

Enforcement was real. The proof includes raw JSONL traces plus `trace_inspection.md` and `guard_events.json`; the run does not rely on exit codes alone.

## Installed vs Repo-Local

- Installed `agentguard` exists, but resolves to a different local checkout, so installed output is comparison evidence only.
- Canonical proof is the repo-local path with `PYTHONPATH=./sdk`; it resolved to this checkout and produced the same demo guard sequence.

## Validation

- Focused pytest slice: `35 passed in 1.51s`.
- Release guard: passed.
- Release/distribution snapshot: GitHub release `v1.2.10`, PyPI `agentguard47==1.2.10`, npm MCP `@agentguard47/mcp-server@0.2.2`.

## Repo Health Notes

- Rolling dogfood issue remains `#490`.
- Green proof PRs continue to wait on human review.
- PR `#531` has failing/cancelled CI checks and should be fixed separately.
- PR `#508` still has failing/cancelled dependency-bump checks.
- Ops-doc freshness remains tracked by issue `#473`.
