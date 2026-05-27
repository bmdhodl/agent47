# Dogfood proof - 2026-05-26 run1

## Scope

SDK-only recurring dogfood run from detached `origin/main` at
`a2d9cce2fa8096d469fafcc8a4de1dac056d3166`.

No dashboard, auth, billing, secret, deployment, paid-feature, or runtime SDK
code was changed.

## Commands

Proof commands:

- `agentguard doctor --trace-file installed_agentguard_doctor_trace.jsonl`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file repo_agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli report repo_coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident repo_coding_agent_review_loop_traces.jsonl`

All proof commands exited `0`; see `command-status.txt`.

## Raw artifacts

- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `repo_coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `repo-demo-report.stdout.txt`
- `repo-demo-incident.stdout.txt`
- `repo-review-loop-report.stdout.txt`
- `repo-review-loop-incident.stdout.txt`
- `open-prs.json`
- `open-issues.json`
- `github-release.json`
- `pypi-agentguard47.txt`
- `npm-mcp-server.txt`
- `glama-agent47.json`
- `mcp-registry-agentguard-search.json`

The review-loop example prints `coding_agent_review_loop_traces.jsonl` because
that is its repo-local default. This run moved that generated file into the
proof bundle as `repo_coding_agent_review_loop_traces.jsonl` so the artifact
name identifies the repo-local proof path.

## Guard behavior observed

Installed `agentguard doctor` and repo-local doctor both emitted
`doctor.verify` start/end spans.

Installed `agentguard demo` emitted:

- `guard.budget_warning`: cost used USD 0.8400 against USD 1.0000 limit.
- `guard.budget_exceeded`: cost used USD 1.0800 > USD 1.0000.
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: `fetch_docs` attempt 3 with limit 2.

Repo-local `python -m agentguard.cli demo` emitted the same four guard events:

- `guard.budget_warning`
- `guard.budget_exceeded`
- `guard.loop_detected`
- `guard.retry_limit_exceeded`

Repo-local `examples/coding_agent_review_loop.py` emitted:

- `guard.budget_exceeded`: review loop stopped on attempt 3 at USD 0.0510 > USD 0.0450.
- `guard.retry_limit_exceeded`: `apply_patch` stopped on attempt 4 with limit 3.

Enforcement was real. The demo and review-loop traces include guard events
created by AgentGuard exceptions and the stdout captures show the loops stopped
at the configured limits.

The review-loop trace intentionally includes both per-iteration costs and the
cumulative `guard.budget_exceeded` cost field. The included review-loop
`report` and `incident` outputs therefore show an inflated estimated cost of
USD 0.1020 from double-counting; the actual enforced cumulative budget stop was
USD 0.0510 > USD 0.0450.

## Validation

- Focused CLI/report/demo/doctor/quickstart tests:
  `43 passed in 1.60s`.
- Full SDK test suite with coverage:
  `761 passed in 16.00s`, total coverage `92.64%`.
- CI tool requirement guard: passed.
- Ruff via `python -m ruff check ...`: passed.
- MCP server tests after `npm --prefix mcp-server ci`:
  `10` node tests passed.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Artifact JSONL parse and guard-event extraction: passed.
- Artifact hygiene was normalized after `command-status.txt` initially had a
  PowerShell UTF-8 BOM.

Two initial test invocations collected zero tests because the paths were wrong
for the repo's `sdk/` pytest root. They were not counted as validation; the
corrected command above is the proof.

`make check` could not run directly because `make` is not installed on this
Windows host, so the equivalent commands were run individually.

## Repo health snapshot

- Open PRs include green but review-required dependency/proof PRs, plus
  failing PR `#508` for the setup-go Dependabot bump.
- PR `#506` remains the older rolling proof PR and still needs human review.
- Issue `#473` already tracks stale ops docs. Current staleness check:
  roadmap is 3 weeks old; architecture is 4 weeks old.
- GitHub release, PyPI, and installed SDK align at `v1.2.10`.
- npm MCP package is `@agentguard47/mcp-server@0.2.2`.
- Glama still reports zero indexed tools.
- MCP Registry search still reports `io.github.bmdhodl/agentguard47` package
  version `0.2.1`, so the known metadata drift remains.

## Next action

Fix or close PR `#508` by updating the CI guardrail expectation for pinned
`actions/setup-go@v6.4.0`, then rerun CI.
