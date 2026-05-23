# AgentGuard Dogfood Proof - 2026-05-23 run2

## Scope

SDK-only local dogfood run from the public AgentGuard checkout. No dashboard,
auth, billing, deployment, secret, paid-feature, or release work was touched.

## Commands

- `python -m pip install -e ./sdk`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `agentguard demo`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

`python -m pip install -e ./sdk` hit the known Windows script replacement
warning for `c:\python313\scripts\agentguard.exe`. The run continued with
`PYTHONPATH=./sdk`, and both `agentguard ...` and `python -m agentguard.cli ...`
commands executed successfully from this checkout.

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
- RetryGuard stopped `fetch_docs` after 3 attempts with limit `2`.

### `coding_agent_review_loop_traces.jsonl`

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement:

- BudgetGuard stopped review attempt 3 at `$0.0510 > $0.0450`.
- RetryGuard stopped `apply_patch` attempt 4 with limit `3`.

## Validation

- Focused SDK proof tests: 35 passed.
- Release guard with MCP npm check: passed.
- `git diff --check`: passed before summary creation.
- Review thread sweep: 23 open PRs inspected, 0 active unresolved non-outdated
  review threads found.

## Repo Health

- GitHub release is `v1.2.10`; PyPI latest/installed package is `1.2.10`.
- npm MCP package is `@agentguard47/mcp-server@0.2.2`; local MCP metadata is
  `0.2.2`.
- Official MCP Registry still reports package version `0.2.1`.
- Glama API still reports `tools: []`.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and
  `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 already tracks this.

## Result

Enforcement was real. This was not just CLI success: raw JSONL events and the
generated report/incident outputs show AgentGuard stopping budget, loop, and
retry failure paths.

## Notes

The review-loop incident report still estimates total cost as `$0.1020` for the
current proof branch while the guard enforced at `$0.0510`. PR #502 already
carries the dogfood cost-accounting fix, so this run did not duplicate it.
