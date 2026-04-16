# Morning Report

## Mission
Strengthen the SDK’s pricing story for token-metered AI APIs by adding a local proof that one oversized turn can trip `BudgetGuard`, then thread that proof into the main onboarding docs.

## What shipped
- added `examples/per_token_budget_spike.py`, a local-only example that prices each turn from token counts and catches a single oversized turn with `BudgetGuard`
- added execution coverage for that example in `sdk/tests/test_example_starters.py`
- updated `README.md`, `docs/guides/getting-started.md`, and `examples/README.md` to frame pricing risk around token-heavy spikes rather than only endless loops
- regenerated `sdk/PYPI_README.md`
- added an unreleased changelog entry and proof bundle under `proof/per-token-budget-spike/`

## Why it matters
- token-metered pricing makes budget spikes a first-order failure mode, not just slow budget drift
- the new example proves the behavior locally with no API key and no provider dependency
- the docs now point to that proof directly, which is stronger for onboarding than abstract pricing copy

## Validation
- `python examples/per_token_budget_spike.py` passed
- `python -m agentguard.cli report proof/per-token-budget-spike/per_token_budget_spike_traces.jsonl` passed
- `python scripts/sdk_preflight.py` passed
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80` passed: `673 passed`, `93.13%` coverage
- `python scripts/sdk_release_guard.py` passed
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q` passed

## Notes
- I intentionally did not touch the landing-page copy in this repo because the queue item’s `bmdpat.com` work belongs outside the SDK boundary
- I avoided the stronger “every provider will follow within 6 months” claim because that would need external verification the repo does not need to ship this improvement
