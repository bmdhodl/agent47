# AG-30 shared local call limit

Copy-and-run demo for the v1.4.0 reservation path. The script imports the
published `agentguard47` 1.4.0 wheel. It does not import the repository
checkout. Each run creates a new temporary store.

```bash
pip install agentguard47==1.4.0
python examples/shared_call_limit.py
```

PowerShell uses the same two commands. This environment executed Linux only
(`Linux-6.12.94+-x86_64-with-glibc2.39`, Python 3.12.3, spawn). Windows was
not executed.

`wheel.txt` records the installed module path. `runs.txt` is two consecutive
runs, both exit 0, both `dispatched=1` and `stopped=1`. `pytest.txt` is the
installed-distribution test plus the proof-gallery path check. `ruff.txt` is
the example and test lint.

Visible text, scanned:

- `Shared local limit: one simulated call was sent. The other worker was stopped before send.`
- `Boundary: one shared local key. Not a provider invoice cap. Not a cross-machine budget.`
- `Next: run this script again. It creates a fresh temporary store, so the last run does not block it.`
- Gallery heading `8. Shared local call limit` and README row `shared_call_limit.py`.

The provider is simulated. No API key, billable request, or network call after
install. This is one shared local key, not an invoice cap and not a
cross-machine budget.
