# AG-03 reservation contract proof

Design-only. `BudgetGuard` is unchanged.

```bash
python proof/ag-03-reservation-contract/concurrent_first_use.py
python -m pytest sdk/tests/test_reservation_contract.py sdk/tests/test_enforcement_boundary.py::test_two_worker_example_characterizes_overshoot -q
python examples/enforcement_boundary/two_worker_overshoot.py
```

Expected: the model admits exactly one of two workers; current `check()` still overshoots.

Capture ruff with `NO_COLOR=1`. Proof text files must stay plain ASCII so
`gh pr diff` for Claude review does not refuse escape sequences.
