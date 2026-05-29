# AgentGuard dogfood run 21 - 2026-05-29

## Scope

- Branch: `dogfood-2026-05-29-run2-worker`
- Commit before run: `11cfa07`
- Purpose: refresh the rolling same-day dogfood proof with installed and repo-local AgentGuard enforcement.
- Non-goals: no SDK runtime changes, no dashboard/auth/billing/secrets/deployment work, no release cut.

## Commands run

- `python -m pip install -e ./sdk` -> exit 0 (`editable-install.out.txt`)
- `C:\Python313\python.exe -c import agentguard...` -> exit 0 (`import-binding.out.txt`)
- `agentguard doctor --trace-file proof/dogfood/2026-05-29/run21/installed_doctor_trace.jsonl --json` -> exit 0 (`installed-doctor.out.txt`)
- `agentguard demo --trace-file proof/dogfood/2026-05-29/run21/installed_demo_trace.jsonl` -> exit 0 (`installed-demo.out.txt`)
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run21/repo_doctor_trace.jsonl --json` -> exit 0 (`repo-doctor.out.txt`)
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-29/run21/repo_demo_trace.jsonl` -> exit 0 (`repo-demo.out.txt`)
- `python examples/coding_agent_review_loop.py` from the run artifact directory -> exit 0 (`review-loop.out.txt`)
- `python -m agentguard.cli report proof/dogfood/2026-05-29/run21/repo_demo_trace.jsonl` -> exit 0 (`demo-report.out.txt`)
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run21/repo_demo_trace.jsonl` -> exit 0 (`demo-incident.out.txt`)
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run21/coding_agent_review_loop_traces.jsonl` -> exit 0 (`review-loop-incident.out.txt`)
- `python -m pytest sdk/tests/test_doctor.py sdk/tests/test_demo.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py sdk/tests/test_sdk_release_guard.py -q` -> exit 0 (`focused-tests.out.txt`)
- `python scripts/sdk_release_guard.py --check-mcp-npm` -> exit 0 (`release-guard.out.txt`)
- Repo health, package, release, registry, PR, issue, and review-thread snapshot commands -> exit 0; full statuses are in `command_statuses.json`.

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

Raw extracted events are in `guard_events.json` and `trace-inspection.json`. Enforcement real: `True`.

## Validation

- Proof commands exited 0.
- Focused proof/metadata tests passed: `36 passed in 0.42s`.
- Release guard MCP npm check: `Release guard passed.`
- `git diff --check` passed.
- Package binding resolved to `sdk/agentguard/__init__.py`, version `1.2.10`.
- Artifact hygiene passed: UTF-8 without BOM, no NUL bytes, JSON/JSONL parse clean.

## Repo health notes

- PR #544 is still green but blocked by required human review: merge `BLOCKED`, review `REVIEW_REQUIRED`.
- PR #544 review sweep found 0 review threads and no REST review comments.
- Open PR review threads needing action: #518 has 1 active thread on stale dogfood proof.
- Roadmap and architecture freshness remain stale: roadmap `3 weeks ago`, architecture `4 weeks ago`; issue #473 tracks this.
- Release/package alignment remains GitHub `v1.2.10`, PyPI/local SDK `1.2.10`, and npm/local MCP server `0.2.2`.
- Official MCP Registry still reports `0.2.1`; Glama API returns env schema with `tools: []`.

## Artifacts

- Raw traces: `installed_doctor_trace.jsonl`, `installed_demo_trace.jsonl`, `repo_doctor_trace.jsonl`, `repo_demo_trace.jsonl`, `coding_agent_review_loop_traces.jsonl`
- Reports/incidents: `demo-report.out.txt`, `demo-incident.out.txt`, `review-loop-incident.out.txt`
- Evidence snapshots: `open-prs.json`, `open-issues.json`, `pr-544-status.json`, `pr-544-review-comments.json`, `pr-544-review-threads.json`, `open-pr-review-threads.json`, `open-pr-review-thread-summary.json`, `github-release.json`, `pypi-agentguard47.out.txt`, `npm-mcp-version.out.txt`, `mcp-registry-search.json`, `glama-api.out.txt`
- Validation: `focused-tests.out.txt`, `release-guard.out.txt`, `git-diff-check.out.txt`, `artifact-hygiene.json`
