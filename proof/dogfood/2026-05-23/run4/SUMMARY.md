# AgentGuard Dogfood Proof - 2026-05-23 run4

## Result

Trace-backed dogfood proof passed. Enforcement was real: the demo and coding-agent review-loop traces contain guard events, not only successful command output.

## Commands

See `command_output.md` for the command list and guard-event summary.

## Raw trace files

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`

## Guard events observed

- `guard.budget_warning`
- `guard.budget_exceeded`
- `guard.loop_detected`
- `guard.retry_limit_exceeded`

## Enforcement conclusion

The run counts as dogfood proof because the raw JSONL traces show BudgetGuard, LoopGuard, and RetryGuard enforcement. The review-loop trace specifically proves coding-agent safety behavior by stopping a budget overrun and a retry storm.

## Validation

See `VALIDATION.md`.

## Repo health snapshot

- Open PR count: 23.
- PR #506: `REVIEW_REQUIRED` / `BLOCKED` before this push, with green CI on the previous commit and no review threads.
- Full open-PR GraphQL sweep: 0 active unresolved non-outdated review threads.
- Open issues still needing action: #473 docs freshness, #469 clean SDK-only pip-audit reproduction, #468 release queue, #464 managed-agent cost surface, #418 dependency drift cleanup.
- Release/package alignment: GitHub release, PyPI, and local SDK are `1.2.10`; npm and local MCP metadata are `0.2.2`.
- Distribution drift remains: MCP Registry reports `0.2.1`; Glama API reports zero indexed tools.