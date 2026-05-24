# Dogfood Operator Run 5 - 2026-05-24

## Scope

SDK-only dogfood proof run for the public AgentGuard47 repo. No dashboard,
auth, billing, secrets, deployments, paid features, runtime code, or release
work was touched.

## Commands Run

- `where.exe agentguard`
- `agentguard doctor --trace-file agentguard_doctor_trace_installed.jsonl`
- `python -m pip install -e ./sdk` after the existing console script failed to
  import `agentguard`
- `agentguard doctor --trace-file agentguard_doctor_trace_installed.jsonl`
- `PYTHONPATH=./sdk python -c "import agentguard; print(agentguard.__file__)"`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `PYTHONPATH=./sdk python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`
- GitHub release, PR, issue, and review-thread checks with `gh`
- PyPI, npm, MCP Registry, and Glama distribution checks

## Guard Behavior Observed

Trace inspection found 10 selected guard or doctor events:

- `agentguard_doctor_trace_installed.jsonl`: two `doctor.verify` events from
  the package-installed CLI path after editable install repaired the broken
  console script.
- `agentguard_doctor_trace.jsonl`: two `doctor.verify` events from the
  repo-local module path.
- `agentguard_demo_traces.jsonl`: `guard.budget_warning` at `$0.8400` against
  the `$1.0000` limit.
- `agentguard_demo_traces.jsonl`: `guard.budget_exceeded` at `$1.0800 >
  $1.0000`.
- `agentguard_demo_traces.jsonl`: `guard.loop_detected` for repeated
  `tool.search`.
- `agentguard_demo_traces.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs`
  attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at `$0.0510
  > $0.0450` on attempt 3.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for
  `apply_patch` attempt 4 with limit 3.

This run counts as real dogfood proof because the raw JSONL traces and
report/incident output show budget, loop, and retry enforcement, not just
successful command exits.

## Validation

- Initial installed CLI doctor: failed before editable install with
  `ModuleNotFoundError: No module named 'agentguard'`; captured as environment
  drift in `installed_agentguard_doctor_output.txt`.
- Editable install: passed.
- Installed CLI doctor after editable install: passed and wrote
  `agentguard_doctor_trace_installed.jsonl`.
- Repo-local doctor/demo/review-loop proof commands: passed.
- Focused proof/CLI/metadata tests: `35 passed in 1.50s`.
- Release guard with MCP npm check: passed.
- `git diff --check`: passed.
- Artifact hygiene: UTF-8/no BOM/no NUL/no local path leaks, JSON/JSONL parse
  passed.
- Open-PR review-thread sweep: 25 open PRs, 56 review threads, 0 active
  unresolved non-outdated threads.

## Repo Health Snapshot

- PR #506 remains the consolidated rolling proof PR and was green before this
  run.
- PR #508 still has failing Python checks from the setup-go Dependabot bump
  guardrail expectation.
- PR #509 and PR #510 are green Dependabot PRs but still require review.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and
  `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 tracks docs freshness.
- Release/package alignment remains GitHub/PyPI/local SDK `1.2.10` and
  npm/local MCP `0.2.2`.
- Distribution drift remains: MCP Registry reports `0.2.1`; Glama API returns
  an empty `tools` array.

## Artifact Index

- `agentguard_doctor_trace_installed.jsonl`
- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- `where_agentguard.txt`
- `installed_agentguard_doctor_output.txt`
- `installed_agentguard_doctor_after_editable_output.txt`
- `pip_install_editable_output.txt`
- `repo_import_output.txt`
- `doctor_output.txt`
- `demo_output.txt`
- `review_loop_output.txt`
- `demo_report_output.txt`
- `demo_incident_output.txt`
- `review_loop_report_output.txt`
- `review_loop_incident_output.txt`
- `pytest_output.txt`
- `release_guard_output.txt`
- `git_diff_check.txt`
- `artifact_hygiene.txt`
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

## Docs Updates Needed

- No docs changes were needed for this proof-only run.
- Existing docs-freshness issue #473 still tracks stale roadmap and
  architecture docs.
