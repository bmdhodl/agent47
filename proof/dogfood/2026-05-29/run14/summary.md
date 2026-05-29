# AgentGuard Dogfood Proof - 2026-05-29 run14

## Scope

- Goal: keep the real AgentGuard dogfood workflow running under the SDK and append proof to the existing rolling PR.
- Scope: proof artifacts only under `proof/dogfood/2026-05-29/run14/`.
- Non-goals: no SDK runtime changes, no dashboard/auth/billing/secrets/deployment work, and no release cut.
- Done criteria: raw traces exist, guard behavior is visible in trace events, focused proof tests pass, release/distribution health is checked, and GitHub issue/PR sinks are updated.

## Commands Run

- `python --version`
- `python -m pip install -e .\sdk`
- `PYTHONPATH=.\sdk python -c "import agentguard ..."`
- `PYTHONPATH=.\sdk agentguard doctor --trace-file proof\dogfood\2026-05-29\run14\agentguard_doctor_trace.path.raw.jsonl --json`
- `PYTHONPATH=.\sdk python -m agentguard.cli doctor --trace-file proof\dogfood\2026-05-29\run14\agentguard_doctor_trace.raw.jsonl --json`
- `PYTHONPATH=.\sdk agentguard demo --trace-file proof\dogfood\2026-05-29\run14\agentguard_demo_traces.path.raw.jsonl`
- `PYTHONPATH=.\sdk python -m agentguard.cli demo --trace-file proof\dogfood\2026-05-29\run14\agentguard_demo_traces.raw.jsonl`
- `PYTHONPATH=.\sdk python examples\coding_agent_review_loop.py`
- `PYTHONPATH=.\sdk python -m agentguard.cli report proof\dogfood\2026-05-29\run14\agentguard_demo_traces.raw.jsonl`
- `PYTHONPATH=.\sdk python -m agentguard.cli incident proof\dogfood\2026-05-29\run14\agentguard_demo_traces.raw.jsonl`
- `PYTHONPATH=.\sdk python -m agentguard.cli incident proof\dogfood\2026-05-29\run14\coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=.\sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py sdk/tests/test_sdk_release_guard.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`

## Guard Behavior Observed

The run is trace-backed, not command-success-only. `guard_events.json` extracted 14 doctor/guard events from raw JSONL traces.

- `doctor.verify` emitted start/end events for both path CLI and module CLI doctor runs.
- Demo proof emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Demo proof emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Demo proof emitted `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- Demo proof emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Review-loop proof emitted `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- Review-loop proof emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Validation

- Proof commands exited 0 after explicitly binding `PYTHONPATH` to this checkout's `sdk/`.
- Active import binding: `<repo>\sdk\agentguard\__init__.py`, version `1.2.10`.
- Focused proof/metadata tests: `36 passed in 1.71s`.
- Release guard with npm MCP check: `Release guard passed.`
- Ops freshness remains stale: roadmap `3 weeks ago`, architecture `4 weeks ago`; tracked by issue #473.

## Release And Distribution

- GitHub release: `v1.2.10`.
- PyPI latest: `1.2.10`.
- Local SDK: `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Local MCP package: `0.2.2`.
- Official MCP Registry search still shows `io.github.bmdhodl/agentguard47` at `v0.2.1`.
- Glama API check timed out from this host during run14, so the prior `tools: []` state remains a follow-up until rechecked.

## Repo Health

- Existing PR #544 is the rolling dogfood PR for 2026-05-29 run2+ proof.
- PR #544 was green before this run and had zero review threads on the pre-run GraphQL sweep.
- PR #508 remains the only visible open PR with failed/cancelled checks and needs separate CI triage.
- Issues #473, #490, #507, #469, #468, #418, #282, and #279 remain real trackers; #512-#515 look like scanner-created tech-debt noise candidates.

## Artifacts

- `agentguard_doctor_trace.path.raw.jsonl`
- `agentguard_doctor_trace.raw.jsonl`
- `agentguard_demo_traces.path.raw.jsonl`
- `agentguard_demo_traces.raw.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `08_demo_report.out.txt`
- `09_demo_incident.out.txt`
- `10_review_loop_incident.out.txt`
- `11_focused_tests.out.txt`
- `12_release_guard_mcp_npm.out.txt`
- `15_release_distribution.out.txt`
- `16_artifact_hygiene.out.txt`
- `17_git_diff_check.out.txt`
