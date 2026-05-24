# Dogfood Proof 2026-05-23 Run 17

## Goal

Keep a real AgentGuard workflow running against this repo and preserve durable proof that the SDK enforces runtime guard behavior.

## Scope

- SDK-only dogfood proof artifacts under `proof/dogfood/2026-05-23/run17/`
- GitHub PR, issue, release, package, and review-thread snapshots
- No SDK runtime, dashboard, auth, billing, deployment, or paid-feature changes

## Commands Run

- `agentguard doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Concrete Guard Behavior Observed

- Demo trace emitted `guard.budget_warning` at `$0.84` of a `$1.00` limit.
- Demo trace emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Demo trace emitted `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- Demo trace emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- Doctor trace emitted `doctor.verify` start and end events for local setup verification.

## Artifact Files

- `agentguard_doctor_console_output.txt`
- `agentguard_doctor_console_trace.jsonl`
- `agentguard_doctor_cli_output.txt`
- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_cli_output.txt`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_output.txt`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.txt`
- `demo_incident.md`
- `review_loop_report.txt`
- `review_loop_incident.md`
- `guard_events.json`
- `open_prs.json`
- `open_issues.json`
- `pr_506_view.json`
- `pr_508_view.json`
- `review_threads.json`
- `review_thread_summary.json`
- `github_release.json`
- `npm_mcp_version.txt`
- `pypi_versions.txt`
- `mcp_registry_search.json`
- `glama_api.json`
- `release_guard.txt`
- `focused_tests.txt`
- `artifact_hygiene.txt`
- `git_diff_check.txt`

## Validation

- Focused proof tests: `35 passed in 1.47s`.
- Release guard: passed.
- Artifact hygiene: 33 files scanned, no local path leaks, no BOMs, no NUL bytes, JSON parse passed.
- `git diff --check`: passed.

## Repo Health Snapshot

- PR #506 remains the consolidated rolling proof PR and is blocked only on required human review.
- Open PR review-thread sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.
- PR #508 still has failing CI from the setup-go Dependabot bump guardrail expectation.
- Roadmap and architecture freshness warnings remain active: roadmap `2 weeks ago`, architecture `3 weeks ago`; issue #473 tracks docs freshness.
- GitHub release, PyPI, and local SDK align at `1.2.10`; npm MCP package is `0.2.2`.
- Official MCP Registry still reports `0.2.1`; Glama still returns `tools: []`.

## Done Criteria

This run is complete because it produced raw trace files, report and incident output, a Markdown proof summary, validation output, repo health snapshots, and a GitHub artifact update path for PR #506 / issue #490.
