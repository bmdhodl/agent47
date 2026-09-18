# Enforcement-boundary examples

Offline reproductions for the [enforcement boundary](../../docs/enforcement-boundary.md).

```bash
python examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py
python examples/enforcement_boundary/two_worker_overshoot.py
```

`exhausted_budget_blocks_dispatch.py` shows an exhausted recorded call budget
blocking the next mocked OpenAI dispatch.

`two_worker_overshoot.py` shows two threads both passing `check()` and both
dispatching. That overshoot is current behavior, not a claimed fix.
