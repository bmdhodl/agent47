# PR Draft

## Title
Align SDK decision traces with dashboard runtime-control contract

## Summary
- make SDK decision-trace helpers emit non-empty dashboard-parseable
  `binding_state` values by default
- extend the local hosted-ingest harness to report decision-trace warnings like
  the dashboard does
- tighten README, SDK README, guides, and examples around the local proof path,
  hosted ingest, decision history, and remote-kill polling boundary

## Scope
- `sdk/agentguard/decision.py`
- hosted-ingest and decision-trace tests
- README / SDK README / quickstart and dashboard-contract docs
- package metadata and generated PyPI README sync

## Non-goals
- no dashboard repo changes
- no new runtime dependencies
- no breaking public API changes
- no automatic remote-kill polling helper in this PR

## Risk
- low runtime risk: decision helpers still emit the same event names and fields,
  but `binding_state` now defaults to a string instead of `None`
- docs now avoid overclaiming remote kill unless an application explicitly polls
  and handles dashboard signals

## Rollback
- revert the PR to restore prior decision payload defaults and docs
- no migrations or package dependency changes are involved

## Validation
- `python -m pytest sdk/tests/test_decision_trace.py sdk/tests/test_hosted_ingest_contract.py -v`
- `python -m pytest sdk/tests/test_exports.py sdk/tests/test_architecture.py -v`
- `python -m ruff check sdk/agentguard/decision.py sdk/tests/conftest.py sdk/tests/test_decision_trace.py sdk/tests/test_hosted_ingest_contract.py`
- `python scripts/generate_pypi_readme.py --write`
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py`
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `npm --prefix mcp-server test`
- `python -m pytest sdk/tests/test_architecture.py -v`
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`
- `python scripts/sdk_release_guard.py`
- `python scripts/sdk_preflight.py`

`make` is unavailable in this Windows shell, so the Makefile-equivalent commands
were run directly.
