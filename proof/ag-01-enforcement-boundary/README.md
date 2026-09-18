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
- `make check`: 1064 passed, 1 skipped, coverage 91%.
- `make structural`: 9 passed.
- `make security`: bandit quiet pass.
- MCP tests: 11 passed, including read-only allow and mutating-name deny.
- Site pages `enforcement.html`, `index.html`, `quickstart.html` at 375/768/1440:
  horizontal overflow 0. Bounds nav from the homepage lands on `/enforcement.html`.
  Favicon 404 only.

No new public SDK API. No `BudgetGuard` reservation. No dashboard revival.
