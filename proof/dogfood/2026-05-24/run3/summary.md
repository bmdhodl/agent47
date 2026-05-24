# Dogfood Operator Run 3 - 2026-05-24

## Scope

SDK-only dogfood proof run for the public AgentGuard47 repo. No dashboard, auth, billing, secrets, deployments, paid features, runtime code, or release work was touched.

## Commands Run

- `where.exe agentguard`
- `agentguard doctor` (installed shim smoke check; failed because the active Python could not import `agentguard`)
- `PYTHONPATH=./sdk python -c "import agentguard; print(agentguard.__file__)"`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `PYTHONPATH=./sdk python scripts/sdk_release_guard.py --check-mcp-npm`
- GitHub release, PR, issue, and review-thread health checks with `gh`
- PyPI, npm, MCP Registry, and Glama distribution checks

## Guard Behavior Observed

Trace inspection found 6 concrete guard events:

- `agentguard_demo_traces.jsonl`: `guard.budget_warning`
- `agentguard_demo_traces.jsonl`: `guard.budget_exceeded` with `Cost budget exceeded: $1.0800 > $1.0000`
- `agentguard_demo_traces.jsonl`: `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`
- `agentguard_demo_traces.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at `$0.0510 > $0.0450` on attempt 3
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3

This run counts as real dogfood proof because the raw JSONL traces and incident/report output show budget, loop, and retry enforcement, not just successful command exits.

## Validation

- Focused proof/CLI/metadata tests: `35 passed in 1.54s`
- Release guard with MCP npm check: passed
- `git diff --check`: passed
- Artifact hygiene: UTF-8/no BOM/no NUL/no local path leaks, JSON/JSONL parse passed
- GitHub release: `v1.2.10`
- PyPI `agentguard47`: latest `1.2.10`
- Local SDK version: `1.2.10`
- npm `@agentguard47/mcp-server`: `0.2.2`
- Local MCP metadata: `0.2.2`
- MCP Registry still reports `0.2.1`
- Glama API still returns an empty `tools` array

## Repo Health Snapshot

- PR #506 remains the consolidated rolling proof PR and was green before this run.
- Open PR sweep found 25 open PRs and 0 active unresolved non-outdated review threads.
- PR #508 still has failing Python checks from the setup-go Dependabot bump guardrail expectation.
- PR #509 and PR #510 are green Dependabot PRs but still require review.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 tracks docs freshness.

## Artifact Index

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- `doctor_output.txt`
- `demo_output.txt`
- `review_loop_output.txt`
- `demo_report_output.txt`
- `review_loop_incident_output.txt`
- `pytest_output.txt`
- `release_guard_output.txt`
- `github_release.json`
- `pypi_agentguard47_versions.txt`
- `npm_mcp_version.txt`
- `mcp_registry_search.json`
- `glama_api.json`
- `open_prs.json`
- `open_issues.json`
- `pr506_snapshot.json`
- `review_thread_summary.json`
- `review_thread_active_summary.json`
- `git_diff_check.txt`
- `artifact_hygiene.txt`
