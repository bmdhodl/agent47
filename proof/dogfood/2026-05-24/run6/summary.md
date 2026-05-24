# Dogfood operator run6 - 2026-05-24

## Goal

Keep a real AgentGuard-protected coding-agent workflow running on the public
SDK repo and leave durable proof that guard enforcement happened.

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-24/run6/agentguard_doctor_trace_installed.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run6/agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run6/agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run6/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run6/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run6/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run6/coding_agent_review_loop_traces.jsonl`

## Guard behavior observed

Raw trace inspection is saved in `trace_inspection.txt` and structured events
are saved in `guard_events.json`.

- Installed doctor emitted `doctor.verify` start/end events.
- Repo-local doctor emitted `doctor.verify` start/end events.
- Demo emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Demo emitted `guard.loop_detected` for repeated `tool.search`.
- Demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

This run counts as real dogfood proof because raw JSONL traces show actual
BudgetGuard, LoopGuard, and RetryGuard enforcement events, not just successful
CLI exits.

## Validation

- Focused proof/CLI/metadata tests: `35 passed in 1.47s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- Artifact hygiene: UTF-8, no BOM, no NUL bytes, JSON/JSONL parse passed, no local path leaks.
- Pre-push open PR review-thread sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.

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
- Issue #511 is a new docs audit for Claude-default assumptions.
