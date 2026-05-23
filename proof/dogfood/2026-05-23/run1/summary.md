# AgentGuard Dogfood Proof - 2026-05-23 run1

## Scope

SDK-only local dogfood run from the public AgentGuard checkout. No dashboard,
secrets, billing, deployment, or release work was touched.

## Commands

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

## Guard Behavior Observed

Raw trace files are saved in this folder.

### `agentguard_demo_traces.jsonl`

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement:

- Budget warning fired at `$0.84` against a `$1.00` limit.
- Budget stop fired at `$1.0800 > $1.0000`.
- LoopGuard stopped repeated `tool.search({"query":"python asyncio"})`.
- RetryGuard stopped `fetch_docs` after it exceeded the retry ceiling.

### `coding_agent_review_loop_traces.jsonl`

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement:

- BudgetGuard stopped review attempt 3 at `$0.0510 > $0.0450`.
- RetryGuard stopped `apply_patch` attempt 4 with limit `3`.

## Result

Enforcement was real. This was not just CLI success: raw JSONL events and the
generated report/incident outputs show AgentGuard stopping budget, loop, and
retry failure paths.

## Notes

The review-loop report still estimates total cost as `$0.1020` for the current
mainline proof path. That drift is already tracked by the existing dogfood cost
accounting fix PR, so this run did not create a duplicate fix.
