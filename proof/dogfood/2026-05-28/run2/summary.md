# Dogfood Proof - 2026-05-28 run2

Host run time: 2026-05-27T22:46:15-05:00. Artifact date follows the UTC automation day.

## Goal

Keep a real AgentGuard workflow running against the public SDK checkout and leave durable proof that runtime guards enforced real stops.

## Scope

- Repo-local SDK proof through `PYTHONPATH=./sdk`
- Generated proof artifacts under `proof/dogfood/2026-05-28/run2/`
- Rolling GitHub dogfood issue update

## Non-goals

- No dashboard, auth, billing, secrets, deployment, paid-feature, or release work
- No SDK runtime changes
- No new dependencies

## Commands Run

- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run2/doctor-trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run2/demo-trace.jsonl`
- From `proof/dogfood/2026-05-28/run2/`: `python ../../../../examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-28/run2/demo-trace.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-28/run2/demo-trace.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_guards.py -q`
- `python scripts/sdk_release_guard.py`

## Guard Behavior Observed

The run produced six concrete guard events in `guard_events.json`:

- `guard.budget_warning`: demo warned at `$0.84 / $1.00`.
- `guard.budget_exceeded`: demo stopped at `$1.08 > $1.00`.
- `guard.loop_detected`: demo stopped repeated `tool.search({"query":"python asyncio"})` on the third repeat.
- `guard.retry_limit_exceeded`: demo stopped `fetch_docs` on attempt 3 with limit 2.
- `guard.budget_exceeded`: review-loop stopped attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: review-loop stopped `apply_patch` on attempt 4 with limit 3.

This counts as real enforcement: the trace files show guard events emitted by AgentGuard and the captured stdout shows the proof flows stopped at the configured budget/retry/loop limits.

## Validation

- Focused pytest: `110 passed in 0.71s`
- Release guard: `Release guard passed.`
- Artifact validation: `artifact validation passed: 6 guard events`
- Local path leak scan: clean
- Release/package snapshot: GitHub release `v1.2.10`, PyPI `agentguard47==1.2.10`, npm `@agentguard47/mcp-server==0.2.2`

`make` is unavailable in this Windows shell, so the release guard was run through its direct underlying command.

## Repo Health Notes

- Repo identity: `bmdhodl/agent47`, default branch `main`, local HEAD `3f54935`.
- Current checkout began detached at `origin/main`; this proof was committed on `dogfood-2026-05-28-run2-worker`.
- Roadmap staleness check: `ops/03-ROADMAP_NOW_NEXT_LATER.md` last touched 3 weeks ago, over the 5 day threshold.
- Architecture staleness check: `ops/02-ARCHITECTURE.md` last touched 4 weeks ago, over the 14 day threshold.
- `ops/FOLLOWUP.md` still points to MCP Registry metadata refresh and Glama tool indexing as the highest distribution hygiene items.

## PR / Issue Snapshot

- PR #532 is green and mergeable but blocked by required human review.
- PR #531 has failing lint/test checks and review comments requiring a regenerated `sdk/PYPI_README.md` plus an executable `BudgetGuard` enforcement snippet.
- Issue #490 remains the rolling dogfood proof log.
- Issue #473 tracks stale ops docs and remains relevant.
- Security/dependency issues #469/#507 remain open and should not be mixed into dogfood artifact PRs.
