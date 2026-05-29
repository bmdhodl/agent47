# AgentGuard dogfood run 19 - 2026-05-29

## Scope

- Branch: `dogfood-2026-05-29-run2-worker`
- Commit before run: `d9943bc`
- Purpose: refresh the rolling same-day dogfood proof with installed and repo-local AgentGuard enforcement.
- Non-goals: no SDK runtime changes, no dashboard/auth/billing/secrets/deployment work, no release cut.

## Commands run

- `python -m pip install -e ./sdk`
- `python -c ...` import binding check with `PYTHONPATH=./sdk`
- `agentguard doctor --trace-file proof/dogfood/2026-05-29/run19/installed_doctor_trace.jsonl --json`
- `agentguard demo --trace-file proof/dogfood/2026-05-29/run19/installed_demo_trace.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run19/repo_doctor_trace.jsonl --json`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-29/run19/repo_demo_trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-29/run19/repo_demo_trace.jsonl`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run19/repo_demo_trace.jsonl`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run19/coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_doctor.py sdk/tests/test_demo.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py sdk/tests/test_sdk_release_guard.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

Full command statuses are in `command_statuses.json`.

## Guard behavior observed

Trace inspection confirmed real guard behavior, not just successful commands:

- `installed_doctor_trace.jsonl`: `doctor.verify` start/end events.
- `installed_demo_trace.jsonl`: `guard.budget_warning` at USD 0.84 of USD 1.00.
- `installed_demo_trace.jsonl`: `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- `installed_demo_trace.jsonl`: `guard.loop_detected` for repeated `tool.search`.
- `installed_demo_trace.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs`.
- `repo_doctor_trace.jsonl`: `doctor.verify` start/end events.
- `repo_demo_trace.jsonl`: the same budget warning, budget exceeded, loop detected, and retry-limit events.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at USD 0.0510 > USD 0.0450 on review attempt 3.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4.

Raw extracted events are in `guard_events.json` and `trace-inspection.json`.

## Validation

- Proof commands exited 0.
- Focused proof/metadata tests passed: `36 passed`.
- Release guard MCP npm check: `Release guard passed.`
- `git diff --check` passed.
- Package binding resolved to `sdk/agentguard/__init__.py`, version `1.2.10`.

## Repo health notes

- PR #544 is still green but blocked by required human review.
- Open PR sweep captured 50 open PRs; active unresolved non-outdated review threads found on: #520 (6), #518 (1).
- Roadmap and architecture freshness remain stale: roadmap `3 weeks ago`, architecture `4 weeks ago`; issue #473 tracks this.
- Release/package alignment remains GitHub `v1.2.10`, PyPI/local SDK 1.2.10, and npm/local MCP server `0.2.2`.
- Official MCP Registry still reports `0.2.1`; Glama API returns `0` indexed tools with environment schema present.

## Artifacts

- Raw traces: `installed_doctor_trace.jsonl`, `installed_demo_trace.jsonl`, `repo_doctor_trace.jsonl`, `repo_demo_trace.jsonl`, `coding_agent_review_loop_traces.jsonl`
- Reports/incidents: `demo-report.out.txt`, `demo-incident.out.txt`, `review-loop-incident.out.txt`
- Evidence snapshots: `open-prs.json`, `open-issues.json`, `review-threads.json`, `github-release.json`, `pypi-agentguard47.out.txt`, `npm-mcp-version.out.txt`, `mcp-registry-search.json`, `glama-api.out.txt`
- Validation: `focused-tests.out.txt`, `release-guard.out.txt`, `git-diff-check.out.txt`
