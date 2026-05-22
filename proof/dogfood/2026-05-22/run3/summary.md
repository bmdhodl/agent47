# AgentGuard Dogfood Proof - 2026-05-22 Run 3

## Scope

SDK-only dogfood run from a repo checkout. No dashboard, auth, billing, secrets,
deployments, paid-feature code, or release work was touched.

Repo-local binding was verified before proof by setting `PYTHONPATH` to the
checkout `sdk` directory and importing `agentguard` from that source tree.

## Commands Run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard Behavior Observed

This run counts as real dogfood proof because the raw JSONL traces contain guard
events, not just successful command output.

`agentguard_demo_traces.jsonl` emitted:

- `guard.budget_warning`: 1, at `$0.84` used of `$1.00`
- `guard.budget_exceeded`: 1, at `$1.0800 > $1.0000`
- `guard.loop_detected`: 1, after repeated `tool.search`
- `guard.retry_limit_exceeded`: 1, for `fetch_docs` attempt 3 with limit 2

`coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded`: 1, on review attempt 3 at `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: 1, for `apply_patch` attempt 4 with limit 3

The incident renderer classified the review-loop proof as `critical` with
primary cause `retry_limit_exceeded` and estimated `$0.0205` saved by stopping
the budget overrun.

## Validation

- Focused proof tests: `35 passed in 1.45s`
- Release/package metadata check: `Release guard passed.`

Freshness warning remains active:

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 13 days old
- `ops/02-ARCHITECTURE.md`: 3 weeks old

## Artifacts

- `commands.log`
- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.md`
- `review_loop_incident.md`
