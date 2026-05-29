# AgentGuard dogfood run 17 - 2026-05-29

## Scope

- Branch: `dogfood-2026-05-29-run2-worker`
- Commit before run: `f049ed4`
- Purpose: refresh the rolling same-day dogfood proof with installed and repo-local AgentGuard enforcement.
- Non-goals: no SDK runtime changes, no dashboard/auth/billing/secrets/deployment work, no release cut.

## Commands run

- `python -m pip install -e ./sdk`
- `python -c "import agentguard, pathlib, importlib.metadata as m; ..."`
- `agentguard doctor --trace-file proof/dogfood/2026-05-29/run17/installed_doctor_trace.jsonl --json`
- `agentguard demo --trace-file proof/dogfood/2026-05-29/run17/installed_demo_trace.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run17/repo_doctor_trace.jsonl --json`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-29/run17/repo_demo_trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-29/run17/repo_demo_trace.jsonl`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run17/repo_demo_trace.jsonl`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run17/coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_doctor.py sdk/tests/test_demo.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py sdk/tests/test_sdk_release_guard.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

Full command statuses are in `command_statuses.json`.

## Guard behavior observed

Trace inspection confirmed real guard behavior, not just successful commands:

- `installed_demo_trace.jsonl`: `guard.budget_warning` at USD 0.84 of USD 1.00.
- `installed_demo_trace.jsonl`: `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- `installed_demo_trace.jsonl`: `guard.loop_detected` for repeated `tool.search`.
- `installed_demo_trace.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs`.
- `repo_demo_trace.jsonl`: the same budget warning, budget exceeded, loop detected, and retry-limit events.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at USD 0.0510 > USD 0.0450 on review attempt 3.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4.

Raw extracted events are in `guard_events.json` and `trace-inspection.json`.

## Validation

- Proof commands exited 0 after clearing an earlier accidental review-loop trace and rerunning the example cleanly.
- Focused proof/metadata tests passed: 36 passed in 0.39s.
- Release guard MCP npm check passed.
- `git diff --check` passed.
- PR review-thread sweep for #544 returned `totalCount: 0`.
- Post-wait closeout found zero PR review comments and zero review threads on #544.
- Refreshed CI and CodeQL checks were green after the proof push.

## Repo health notes

- PR #544 is still green but blocked by required human review.
- PR #508 still has failed/cancelled CI and needs separate dependency CI triage.
- Roadmap and architecture freshness remain stale: roadmap 3 weeks old, architecture 4 weeks old; issue #473 tracks this.
- Release/package alignment remains GitHub/PyPI/local SDK 1.2.10 and npm/local MCP server 0.2.2.
- Official MCP Registry still reports 0.2.1; Glama API returned HTTP 403 from this environment.

## Artifacts

- Raw traces: `installed_doctor_trace.jsonl`, `installed_demo_trace.jsonl`, `repo_doctor_trace.jsonl`, `repo_demo_trace.jsonl`, `coding_agent_review_loop_traces.jsonl`
- Reports/incidents: `demo-report.out.txt`, `demo-incident.out.txt`, `review-loop-incident.out.txt`
- Evidence snapshots: `open-prs.json`, `open-issues.json`, `github-release.json`, `pypi-agentguard47.txt`, `npm-mcp-version.txt`, `mcp-registry-search.json`, `glama-api.err.txt`
- Validation: `focused-tests.txt`, `release-guard.txt`, `git-diff-check.txt`, `pr-544-checks-final.txt`
