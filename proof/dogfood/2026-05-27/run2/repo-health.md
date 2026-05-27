# Repo Health Snapshot - 2026-05-27 run2

## Open PRs

- PR #518 `Add dogfood proof for 2026-05-27 run1`: mergeable, CI/CodeQL green, review required. Copilot left one actionable review comment about review-loop cost double counting.
- PR #517 `Add dogfood proof for 2026-05-26 run2`: mergeable, CI/CodeQL green, review required.
- PR #516 `Add dogfood proof for 2026-05-26 run1`: mergeable, CI/CodeQL green, review required.
- PR #510 `chore(deps): bump qs from 6.15.0 to 6.15.2 in /mcp-server`: mergeable, CI/CodeQL green, review required.
- PR #509 `chore(deps): bump github/codeql-action from 4.35.3 to 4.36.0`: mergeable, CI/CodeQL green, review required.
- PR #508 `chore(deps): bump actions/setup-go from 5.6.0 to 6.4.0`: mergeable, review required; previous worker memory still recommends updating the setup-go guardrail expectation to pinned v6.4.0 SHA.

## Open Issues Needing Attention

- Issue #490 `Dogfood operator rolling proof log`: rolling sink for dogfood proof.
- Issue #473 `[ops-cadence] Docs need refresh`: tracks stale ops docs. Current staleness check: roadmap last changed 3 weeks ago; architecture last changed 4 weeks ago.
- Issue #507 and #469: security/dependency audit findings remain open.
- Issue #418: weekly dependency drift report remains open.

## Distribution Health

- GitHub release: `v1.2.10`, published 2026-05-02.
- PyPI `agentguard47`: latest `1.2.10`; installed `1.2.10`.
- npm `@agentguard47/mcp-server`: latest `0.2.2`.
- Official MCP Registry: still reports `@agentguard47/mcp-server` version `0.2.1`.
- Glama API: listing is live with environment schema, but `tools` is still `[]`.

## Validation

- `agentguard doctor` and `agentguard demo` ran from the active checkout after `python -m pip install -e ./sdk`.
- `python examples/coding_agent_review_loop.py` generated fixed review-loop proof.
- Guard-event validation confirmed required demo and review-loop events.
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_example_starters.py::test_coding_agent_review_loop_example_runs_offline sdk/tests/test_example_starters.py::test_coding_agent_review_loop_sample_incident_is_in_sync -q`: 5 passed.
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`: 761 passed, 92.62% coverage.
- `python -m ruff check ...`: passed.
- `python -m pytest sdk/tests/test_architecture.py -v`: 9 passed.
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`: passed.
- `npm --prefix mcp-server ci`: completed; npm audit reported 1 moderate and 1 high vulnerability in dev/MCP dependencies.
- `npm --prefix mcp-server test`: 10 passed.
- `python scripts/sdk_preflight.py`: passed.

## Next Recommended Task

Address PR #508 by updating the setup-go guardrail expectation to the pinned
v6.4.0 SHA, then rerun CI.
