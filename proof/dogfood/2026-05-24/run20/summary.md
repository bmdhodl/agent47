# Dogfood Proof - 2026-05-24 Run 20

## Goal

Keep a real AgentGuard-protected workflow running on the public SDK repo and
leave durable proof that guards enforced behavior, not just that commands ran.

## Commands Run

- `agentguard doctor --trace-file installed_agentguard_doctor_trace.jsonl`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file repo_agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `PYTHONPATH=./sdk python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard Behavior Observed

Proof is trace-backed.

- Installed `agentguard doctor` emitted `doctor.verify` start/end spans.
- Installed `agentguard demo` emitted `guard.budget_warning` at USD 0.8400 / USD 1.0000.
- Installed `agentguard demo` emitted `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- Installed `agentguard demo` emitted `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- Installed `agentguard demo` emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Repo-local doctor/demo emitted the same doctor, budget, loop, and retry guard behavior with `PYTHONPATH=./sdk`.
- Repo-local coding-agent review loop emitted `guard.budget_exceeded` at USD 0.0510 > USD 0.0450.
- Repo-local coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Artifacts

- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- `demo-report.txt`
- `demo-incident.txt`
- `review-loop-incident.txt`
- `focused-tests.txt`
- `release-guard.txt`
- `pre_push_review_thread_summary.json`
- release, distribution, PR, and issue snapshots in this directory

## Validation

- Focused proof/CLI/metadata tests: `35 passed in 1.54s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed before summary cleanup.
- Pre-push review-thread sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.

## Repo Health Snapshot

- GitHub release, PyPI latest, and local SDK metadata align at `1.2.10`.
- npm MCP package and local MCP metadata align at `0.2.2`.
- Official MCP Registry still reports `io.github.bmdhodl/agentguard47` / `@agentguard47/mcp-server` at `0.2.1`.
- Glama API still exposes env schema; tool indexing remains a follow-up item.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 already tracks docs freshness.
- PR #508 remains the concrete failing PR from the setup-go Dependabot bump; PRs #509 and #510 are green but review-required.
- Issues #512-#515 look like tech-debt scanner noise from docs/proof artifacts and need triage.

## Enforcement Verdict

Real enforcement observed. This run counts as dogfood proof because the raw
JSONL traces include budget, loop, and retry guard events from both the demo
path and the repo-local coding-agent review-loop path.
