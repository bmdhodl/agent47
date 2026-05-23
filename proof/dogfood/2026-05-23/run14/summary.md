# AgentGuard dogfood proof - 2026-05-23 run14

## Commands run

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`

## Guard behavior observed

- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo enforcement stopped budget at `$1.0800 > $1.0000`, stopped repeated `tool.search`, and stopped `fetch_docs` after the retry limit.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` and `guard.retry_limit_exceeded` for `apply_patch` attempt 4.
- Doctor output verified local setup and wrote `agentguard_doctor_trace.jsonl`.

## Validation

- Focused SDK proof tests: `35 passed in 1.47s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- Open PR review-thread sweep: 0 active unresolved non-outdated threads.

## Repo health

- PR #506 remains the consolidated rolling proof PR and was green before this push.
- PR #508 is still failing CI from the setup-go Dependabot bump guardrail expectation.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 tracks docs freshness.
- GitHub release/PyPI/local SDK metadata align at `1.2.10`; npm/local MCP metadata align at `0.2.2`.

## Result

Enforcement was real. This was not stdout-only proof; raw JSONL traces, guard-event extraction, report output, incident reports, validation output, and repo-health snapshots are saved in this folder.
