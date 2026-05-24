# AgentGuard dogfood proof - 2026-05-24 run2

## Goal

Keep the public SDK dogfood path running from this checkout and prove that
AgentGuard still emits real guard behavior, not just successful command output.

## Scope

- Repo-local SDK import with `PYTHONPATH=<repo>/sdk`.
- Local-only CLI proof: `doctor`, `demo`, `report`, and `incident`.
- Repo-local coding-agent review-loop proof.
- Repo health snapshots for open PRs, open issues, release/package alignment,
  and review-thread state.

## Non-goals

- No dashboard, auth, billing, deployment, paid feature, or release work.
- No new guard or SDK feature work.
- No dependency changes.

## Commands run

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard behavior observed

`agentguard_demo_traces.jsonl` emitted real guard events:

- `guard.budget_warning=1`
- `guard.budget_exceeded=1` at `$1.0800 > $1.0000`
- `guard.loop_detected=1` for repeated `tool.search`
- `guard.retry_limit_exceeded=1` for `fetch_docs`

`coding_agent_review_loop_traces.jsonl` emitted real guard events:

- `guard.budget_exceeded=1` at `$0.0510 > $0.0450` on review attempt 3
- `guard.retry_limit_exceeded=1` for `apply_patch` attempt 4

`agentguard_doctor_trace.jsonl` emitted local setup verification events.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace-inspection.txt`
- `command-output.txt`
- `demo-report.md`
- `demo-incident.md`
- `review-loop-incident.md`
- `validation-output.txt`
- `github-release.json`
- `release-distribution-snapshot.txt`
- `open-prs.json`
- `open-issues.json`
- `pr-506-state.json`
- `pr-506-checks.txt`
- `review-thread-sweep.json`

## Validation

- Focused dogfood/CLI/metadata tests: `35 passed`.
- Release guard: passed.
- `git diff --check`: passed.
- Artifact hygiene: UTF-8, no BOMs, no NUL bytes, JSON/JSONL parse passed,
  and no machine-local checkout paths remain in text artifacts.

## Repo health notes

- PR #506 remains the consolidated rolling proof PR and is blocked on required
  human review.
- PR #508 still has failing Python checks from the `actions/setup-go` Dependabot
  bump guardrail expectation.
- GitHub release, PyPI, and local SDK metadata align at `1.2.10`.
- npm and local MCP metadata align at `0.2.2`.
- Official MCP Registry search still reports `0.2.1`.
- Glama API returned HTTP 403 from this environment, so tool indexing could not
  be revalidated live in this run.
- Roadmap and architecture freshness warnings remain active: roadmap is
  `2 weeks ago`, architecture is `3 weeks ago`; issue #473 tracks this.
