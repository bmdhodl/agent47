# AgentGuard Dogfood Proof - 2026-05-29 run8

## Scope

- Goal: keep a real AgentGuard-protected workflow running on this repo and publish durable proof.
- Scope: repo-local proof artifacts under `proof/dogfood/2026-05-29/run8/` and GitHub proof sinks.
- Non-goals: no SDK feature work, dashboard work, auth/billing/secrets work, deployment work, or release cutting.
- Done criteria: fresh trace files show real guard behavior; command output, report, incident, and repo-health evidence are saved; validation passes; PR/issue sinks are updated.

## Commands Run

See `command_status.txt` and `*.out.txt` for raw output.

- `python -m pip install -e ./sdk`
- `agentguard doctor --trace-file agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file agentguard_doctor_trace_repo_local.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file agentguard_demo_traces_repo_local.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

All proof commands exited `0`.

## Guard Behavior Observed

This run counted as real dogfood proof because the fresh traces contain guard events, not only normal command success.

- Installed and repo-local demo emitted `guard.budget_warning` at `$0.84 / $1.00`.
- Installed and repo-local demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Installed and repo-local demo emitted `guard.loop_detected` for repeated `tool.search` calls.
- Installed and repo-local demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt `3` with limit `2`.
- Coding-agent review-loop proof emitted `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- Coding-agent review-loop proof emitted `guard.retry_limit_exceeded` for `apply_patch` attempt `4` with limit `3`.

`guard_events.json` contains 36 guard-related rows. Event names seen: `coding_agent.review_loop.budget, coding_agent.review_loop.retry_storm, demo.budget_guard, demo.loop_guard, demo.retry_guard, guard.budget_exceeded, guard.budget_warning, guard.loop_detected, guard.retry_limit_exceeded, tool.retry`.

## Repo Health Evidence

- PR #544: `Add dogfood proof for 2026-05-29 runs 2-7` / `REVIEW_REQUIRED` / `BLOCKED`.
- PR #544 checks at capture time: `{'SUCCESS': 14}`.
- PR #544 review threads: `0`.
- Release/package evidence saved in `github_release.json`, `pypi_versions.txt`, `npm_mcp_version.txt`, `local_mcp_version.txt`, and `local_sdk_version.txt`.
- Staleness evidence saved in `roadmap_staleness.txt` and `architecture_staleness.txt`.
- Open PR and issue snapshots saved in `open_prs.json` and `open_issues.json`.

## Validation

- Focused SDK proof/metadata test slice passed: `103 passed in 0.55s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm` passed.
- Artifact hygiene passed: UTF-8, no BOM/NUL, JSON/JSONL parse, and repo-root scrub.

## Current Findings

- SDK release alignment remains `1.2.10` across GitHub/PyPI/local checkout.
- MCP npm/local package remains `0.2.2`.
- Ops roadmap and architecture are stale (`3 weeks ago` / `4 weeks ago`) and remain tracked by issue #473.
- Open PR #508 still has failed/cancelled CI jobs and needs separate dependency-PR triage.
- Proof PR #544 is green and review-blocked only.
