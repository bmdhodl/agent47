# Incident Dashboard Handoff Validation

## Scope

Copy and report-rendering only. No SDK runtime enforcement behavior, public API,
dependencies, hosted ingest contract, telemetry, dashboard code, or package
metadata changed.

Changed:

- `sdk/agentguard/reporting.py`
- `sdk/tests/test_reporting.py`
- `docs/examples/coding-agent-review-loop-incident.md`
- `CHANGELOG.md`

## Runtime Proof

Command:

```text
$env:PYTHONPATH='sdk'
python examples\coding_agent_review_loop.py
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

Relevant incident output:

```text
- Keep one-off investigations local; add HttpSink only when future incidents need retained history, alerts, or team-visible follow-up.

Keep this report local if it is a one-off investigation. Add hosted ingest only when future incidents need retained history, alerts, spend trends, or team-visible follow-up:

from agentguard import Tracer, HttpSink
tracer = Tracer(sink=HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_..."))

TRACE_EXISTS=True
```

## Checks

```text
python -m pytest sdk\tests\test_reporting.py sdk\tests\test_example_starters.py::test_coding_agent_review_loop_sample_incident_is_in_sync -v
9 passed.

python -m ruff check sdk\agentguard\reporting.py sdk\tests\test_reporting.py
All checks passed.

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_preflight.py
All checks passed.

git diff --check
passed.

make check
not run: `make` is not installed in this PowerShell environment.

Equivalent direct gate:

python -m ruff check sdk\agentguard scripts\generate_pypi_readme.py scripts\sdk_preflight.py scripts\sdk_release_guard.py
All checks passed.

python -m pytest sdk\tests\ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
702 passed, total coverage 92.98%.

npm --prefix mcp-server test
5 passed.
```
