# PR Draft

## Title
Add a local per-token budget spike proof and tighten pricing framing

## Summary
- add a local `per_token_budget_spike.py` example that prices turns from token counts and shows `BudgetGuard` catching one oversized turn
- update README, getting-started docs, and examples docs so the pricing story is about token-metered cost spikes, not just endless loops
- regenerate the PyPI README and add test coverage for the new example

## Scope
- `examples/per_token_budget_spike.py`
- `sdk/tests/test_example_starters.py`
- `README.md`
- `docs/guides/getting-started.md`
- `examples/README.md`
- `CHANGELOG.md`
- `sdk/PYPI_README.md`
- `PR_DRAFT.md`
- `MORNING_REPORT.md`
- proof artifacts under `proof/per-token-budget-spike/`

## Non-goals
- no dashboard work
- no landing-page or `bmdpat.com` copy changes
- no new runtime guard implementation
- no speculative provider-pricing claims that require external verification

## Proof
- `python examples/per_token_budget_spike.py`
- `python -m agentguard.cli report proof/per-token-budget-spike/per_token_budget_spike_traces.jsonl`
- `python scripts/sdk_preflight.py`
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q`

## Saved artifacts
- `proof/per-token-budget-spike/example-output.txt`
- `proof/per-token-budget-spike/per_token_budget_spike_traces.jsonl`
- `proof/per-token-budget-spike/report.txt`
- `proof/per-token-budget-spike/preflight.txt`
- `proof/per-token-budget-spike/tests.txt`
- `proof/per-token-budget-spike/check.txt`
- `proof/per-token-budget-spike/lint.txt`
- `proof/per-token-budget-spike/release-guard.txt`
- `proof/per-token-budget-spike/security.txt`
