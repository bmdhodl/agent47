# Demo Next Activation Validation

## Scope

Activation copy only. No SDK runtime behavior, public API, dependencies,
network behavior, dashboard behavior, or package metadata changed.

Changed:

- `sdk/agentguard/demo.py`
- `sdk/tests/test_demo.py`
- `CHANGELOG.md`

## Manual Runtime Proof

Command:

```text
$env:PYTHONPATH='sdk'; python -m agentguard.cli demo --trace-file <temp>\demo.jsonl
```

Relevant output:

```text
Local proof complete.
Trace written to: <temp>\demo.jsonl
View summary: agentguard report <temp>\demo.jsonl
View incident report: agentguard incident <temp>\demo.jsonl

Next: add AgentGuard to a repo
  agentguard quickstart --framework raw --write
  python agentguard_raw_quickstart.py
  agentguard report .agentguard/traces.jsonl
SDK gives you local enforcement. The dashboard adds alerts, retained history, and remote controls.
TRACE_EXISTS=True
```

## Checks

```text
python -m pytest sdk\tests\test_demo.py -v
2 passed

python -m ruff check sdk\agentguard\demo.py sdk\tests\test_demo.py
All checks passed.

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_preflight.py
All checks passed.

make check
not run: `make` is not installed in this PowerShell environment.

Equivalent direct gate:

python -m ruff check sdk\agentguard scripts\generate_pypi_readme.py scripts\sdk_preflight.py scripts\sdk_release_guard.py
All checks passed.

python -m pytest sdk\tests\ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
701 passed, total coverage 92.98%.

npm --prefix mcp-server test
5 passed.

git diff --check
passed
```
