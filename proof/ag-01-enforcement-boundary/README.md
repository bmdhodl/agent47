# AG-01 enforcement boundary proof

Issue: https://github.com/bmdhodl/agent47/issues/730
Parent: https://github.com/bmdhodl/agent47/issues/729

## Commands

```bash
python examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py
python examples/enforcement_boundary/two_worker_overshoot.py
python -m pytest sdk/tests/test_enforcement_boundary.py -q
make check
make structural
make security
npm --prefix mcp-server test
```

## Results (2026-09-18)

- Exhausted recorded budget blocked the next mock dispatch (`exhausted.json`).
- Two-worker `check()` overshoot observed and labeled not-fixed (`overshoot.json`).
- `make check`: 1068 passed, 1 skipped, coverage 91%.
- `make structural`: 9 passed.
- `make security`: bandit quiet pass.
- MCP tests: 11 passed, including read-only allow and mutating-name deny.
- Site pages `enforcement.html`, `index.html`, `quickstart.html` at 375/768/1440:
  horizontal overflow 0. Bounds nav from the homepage lands on `/enforcement.html`.
  Favicon 404 only.
- Independent QA follow-up: Loop/timeout/rate classified as recorded-event
  preflight; CLI demo budget path classified advisory; LangGraph docs use
  `max_calls`; installed-artifact test pip-installs `./sdk` into an isolated
  `--target` and runs examples without repo `PYTHONPATH=sdk`.
- Independent GPT reviewer signed off SHA `ab1937856fac470123208b097b4d6d835a0837c9`.
- Showwork `ag-01-qa-r3`, `ag-01-qa-r4`, and `ag-01-qa-r6` finished GREEN.
  `ag-01-qa-fixes`, `ag-01-qa-r2`, and `ag-01-qa-r5` are blocked process
  artifacts (require-before-claim ordering); they are not a product gap.
- `BudgetGuard.reset()` exists in `sdk/agentguard/guards.py`; the cost-guardrails
  FAQ is describing current code, not a new API from this PR.

No new public SDK API. No `BudgetGuard` reservation. No dashboard revival.
