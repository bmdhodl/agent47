# Pydantic AI Starter Validation

## Scope

Docs/example growth item only. No SDK runtime behavior, public API, package
metadata, dashboard behavior, telemetry, or hard dependency changed.

Changed:

- `examples/starters/agentguard_pydantic_ai_quickstart.py`
- `examples/starters/README.md`
- `examples/README.md`
- `sdk/tests/test_example_starters.py`
- `CHANGELOG.md`

## External Docs Checked

Pydantic AI official docs were checked for current API shape:

- `Agent.run_sync(...)` is the synchronous run path.
- `pydantic_ai.models.test.TestModel` is the local testing/development model
  for avoiding real model requests.

## Runtime Proof

Absent optional dependency:

```text
$env:PYTHONPATH='sdk'; python examples\starters\agentguard_pydantic_ai_quickstart.py
Install with: pip install agentguard47 pydantic-ai
```

Isolated optional-dependency venv:

```text
python -m venv <temp-venv>
<temp-venv>\Scripts\python.exe -m pip install -e .\sdk pydantic-ai
<temp-venv>\Scripts\python.exe examples\starters\agentguard_pydantic_ai_quickstart.py

Add AgentGuard around the agent run and inspect the local trace.
Traces saved to .agentguard/traces.jsonl
TRACE_EXISTS=True
```

## Checks

```text
python -m ruff check examples\starters\agentguard_pydantic_ai_quickstart.py sdk\tests\test_example_starters.py
All checks passed.

python -m pytest sdk\tests\test_example_starters.py -v
8 passed.

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
702 passed, total coverage 92.98%.

npm --prefix mcp-server test
5 passed.

git diff --check
passed.
```
