# PR Draft

## Title
Add session-level trace correlation for disposable managed-agent harnesses

## Summary
- add optional `session_id` support to `Tracer`, `AsyncTracer`, and `agentguard.init(...)` so one higher-level agent session can span multiple disposable harnesses without losing local correlation
- keep the feature local-first and provider-agnostic: no new sink types, no Anthropic-specific code, and no repo-config or hosted dependency changes
- add guide/example proof so developers can model a managed-agent session with two independent tracer instances in one local file

## Scope
- core tracer plumbing in `sdk/agentguard/tracing.py`, `sdk/agentguard/atracing.py`, and `sdk/agentguard/setup.py`
- focused tests in `sdk/tests/test_tracing.py`, `sdk/tests/test_atracing.py`, `sdk/tests/test_init.py`, and `sdk/tests/test_example_starters.py`
- onboarding docs in `README.md`, `docs/guides/getting-started.md`, `docs/guides/coding-agents.md`, and `docs/guides/managed-agent-sessions.md`
- example updates in `examples/disposable_harness_session.py` and `examples/README.md`
- generated `sdk/PYPI_README.md`
- proof artifacts under `proof/session-id/`

## Non-goals
- no dashboard work
- no Anthropic-managed-agent adapter or vendor-specific instrumentation
- no repo-level persistent `session_id` config in `.agentguard.json`
- no new runtime dependencies
- no trace schema redesign beyond adding an optional correlation field

## Proof
- `python -m ruff check sdk/agentguard/tracing.py sdk/agentguard/atracing.py sdk/agentguard/setup.py sdk/tests/test_tracing.py sdk/tests/test_atracing.py sdk/tests/test_init.py sdk/tests/test_example_starters.py`
- `python -m pytest sdk/tests/test_tracing.py sdk/tests/test_atracing.py sdk/tests/test_init.py sdk/tests/test_example_starters.py -v`
- `python scripts/sdk_preflight.py`
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q`
- proof files:
  - `proof/session-id/example-output.txt`
  - `proof/session-id/managed_session_traces.jsonl`

## Operator note
- local validation pinned `PYTHONPATH=<repo>/sdk` because this machine has another editable `agentguard47` install that can shadow branch code
