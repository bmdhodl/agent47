# Dogfood proof - 2026-05-24 run16

## Goal

Keep the AgentGuard SDK dogfood loop running against the public SDK checkout and leave durable proof that real guard enforcement still works.

## Commands run

- `python -m pip install -e ./sdk`
- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard behavior observed

The run produced real guard events in JSONL traces, not just successful command exits.

- Installed and repo-local doctor emitted `doctor.verify` start/end spans.
- Installed and repo-local demo emitted `guard.budget_warning` at USD 0.8400 / USD 1.0000.
- Installed and repo-local demo emitted `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- Installed and repo-local demo emitted `guard.loop_detected` for repeated `tool.search`.
- Installed and repo-local demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at USD 0.0510 > USD 0.0450.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

Enforcement was real: yes.

## Artifacts

- Raw traces: `installed_doctor_trace.jsonl`, `installed_demo_traces.jsonl`, `repo_doctor_trace.jsonl`, `repo_demo_traces.jsonl`, `review_loop_traces.jsonl`
- Command outputs: `installed_doctor_output.txt`, `installed_demo_output.txt`, `repo_doctor_output.txt`, `repo_demo_output.txt`, `review_loop_output.txt`
- Reports/incidents: `repo_demo_report.txt`, `review_loop_incident.txt`
- Parsed evidence: `guard_events.json`, `trace_inspection.txt`
- Health snapshots: `open_prs.json`, `open_issues.json`, `github_release.json`, `pr506_snapshot.json`
- Distribution snapshots: `pypi_versions.txt`, `npm_mcp_metadata.json`, `npm_mcp_version.txt`, `glama_api.json`, `mcp_registry_direct_error.txt`
- Validation: `focused_tests.txt`, `release_guard.txt`, `git_diff_check.txt`, `artifact_hygiene.txt`

## Validation result

- Focused SDK proof tests: 35 passed.
- Release guard: passed.
- Git diff whitespace check: passed.
- Artifact hygiene: passed after normalizing generated proof files to UTF-8 and scrubbing local worktree prefixes.

## Repo health notes

- PR #506 remains the rolling dogfood proof PR and is green but requires human review.
- PR #508 still has failing/cancelled Python CI for the `actions/setup-go` Dependabot bump.
- PRs #509 and #510 are green Dependabot PRs that still require review.
- Issue #473 still tracks stale ops docs; roadmap is 2 weeks old and architecture is 3 weeks old.
- Release/package alignment remains SDK `1.2.10` and MCP npm package `0.2.2`; Glama/MCP registry indexing remains a distribution follow-up.
