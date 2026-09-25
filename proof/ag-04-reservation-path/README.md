# AG-04 reservation path proof

Sync, non-streaming OpenAI Chat Completions with a shared `JsonFileStateStore`
reserve before send. Two spawned processes and `max_calls=1` produce one mock
dispatch. `check()` and `consume()` still overshoot. This is not an invoice cap.

```bash
python examples/enforcement_boundary/reserved_one_dispatch.py
python -m pytest sdk/tests/test_reservation_path.py -q
```

`race.json` is the script stdout from this environment (Linux, spawn).
Windows was not executed here. The lock file is `JsonFileStateStore`.

Installed-package coverage is
`sdk/tests/test_enforcement_boundary.py::test_examples_run_from_installed_distribution`,
which pip-installs `sdk/` to a temp target and runs the race from that import
path.
