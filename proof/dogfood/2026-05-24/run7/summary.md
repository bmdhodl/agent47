# Dogfood operator run7 - 2026-05-24

## Goal

Keep a real AgentGuard-protected coding-agent workflow running on the public
SDK repo and leave durable proof that guard enforcement happened.

## Commands run

- `python -m pip install -e ./sdk`
- `where.exe agentguard`
- `agentguard doctor --trace-file proof/dogfood/2026-05-24/run7/agentguard_doctor_trace_installed.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-24/run7/agentguard_demo_traces_installed.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run7/agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run7/agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run7/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run7/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run7/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run7/coding_agent_review_loop_traces.jsonl`

## Guard behavior observed

Raw trace inspection is saved in `trace_inspection.txt` and structured events
are saved in `guard_events.json`.

- Installed doctor emitted `doctor.verify` start/end events.
- Repo-local doctor emitted `doctor.verify` start/end events.
- Installed demo emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Installed demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Installed demo emitted `guard.loop_detected` for repeated `tool.search`.
- Installed demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Repo-local demo emitted the same budget, loop, and retry guard events.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

This run counts as real dogfood proof because raw JSONL traces show actual
BudgetGuard, LoopGuard, and RetryGuard enforcement events, not just successful
CLI exits.

## Validation

- Focused proof/CLI/metadata tests: `36 passed in 0.46s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- Artifact hygiene: UTF-8, no BOM, no NUL bytes, JSON/JSONL parse passed.
- `git diff --check`: passed.
- Pre-push open PR review-thread sweep: 25 open PRs, 0 active unresolved non-outdated threads.

## Release and distribution snapshot

- GitHub release: `v1.2.10`.
- PyPI `agentguard47`: latest and installed `1.2.10`.
- Local SDK package version: `1.2.10`.
- npm/local MCP package: `0.2.2`.
- Official MCP Registry search still reports `0.2.1`.
- Glama API still returns an empty `tools` array.

## Repo health notes

- PR #506 remains the consolidated rolling proof PR and is blocked only by required human review.
- PR #508 still has failing Python checks from the setup-go Dependabot bump guardrail expectation.
- PR #509 and PR #510 are green Dependabot PRs but require review.
- Issue #473 still tracks stale roadmap/architecture docs.
- Issue #507 and issue #469 remain security/dependency audit sinks.
- Issue #511 tracks the new docs audit for Claude-default assumptions.
