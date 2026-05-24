# Dogfood proof - 2026-05-24 run1

## Scope

Recurring AgentGuard dogfood run for the public SDK repo. SDK-only. No dashboard, auth, billing, deployment, secret, or paid-feature code touched.

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-24/run1/agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run1/python_module_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run1/agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run1/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run1/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run1/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run1/coding_agent_review_loop_traces.jsonl`
- `python -m pytest tests/test_demo.py tests/test_doctor.py tests/test_cli_report.py tests/test_guards.py -q` from `sdk/`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- GitHub release, PyPI, npm, open issue, open PR, and review-thread health snapshots

## Concrete guard behavior observed

Trace inspection found the required guard behavior in raw JSONL output.

Demo trace:

- `guard.budget_warning`: 1 event at `$0.84 / $1.00`
- `guard.budget_exceeded`: 1 event at `$1.0800 > $1.0000`
- `guard.loop_detected`: 1 event for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: 1 event for `fetch_docs` attempt 3 with limit 2

Coding-agent review-loop trace:

- `guard.budget_exceeded`: 1 event on review attempt 3 at `$0.0510 > $0.0450`, `12300` tokens used
- `guard.retry_limit_exceeded`: 1 event for `apply_patch` attempt 4 with limit 3

Doctor traces emitted setup verification events but no guard enforcement events, as expected.

## Artifacts

- `agentguard_doctor_trace.jsonl` and `python_module_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- `demo_report.txt` and `demo_incident.txt`
- `review_loop_report.txt` and `review_loop_incident.txt`
- `focused_tests.txt`
- `release_guard_mcp_npm.txt`
- `github_release.json`, `pypi_agentguard47_versions.txt`, and `npm_mcp_server.json`
- `open_prs.json`, `open_issues.json`, `review_threads.json`, `review_thread_summary.json`, and `git_diff_check.txt`
- roadmap and architecture staleness snapshots

## Validation

- Focused SDK proof tests: `110 passed in 0.66s`
- Release guard MCP/npm metadata check: passed
- Trace parser check: passed and failed closed if required guard events were missing
- Open PR review-thread sweep: `25` PRs scanned, `56` threads scanned, `0` active unresolved non-outdated threads
- `git diff --check`: passed

## Repo health snapshot

- GitHub release, PyPI, and local package metadata are aligned at `agentguard47` `1.2.10`.
- npm and local MCP package metadata are aligned at `@agentguard47/mcp-server` `0.2.2`.
- PR #506 remains the consolidated rolling proof PR and is blocked only by required human review before this run's new push.
- PR #508 still has failing Python checks from the setup-go Dependabot bump guardrail expectation.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 already tracks docs freshness.

## Next action

Fix PR #508 by updating `sdk/tests/test_ci_guardrails.py` to expect the pinned setup-go v6.4.0 action string, then rerun that PR's focused guardrail test and CI.