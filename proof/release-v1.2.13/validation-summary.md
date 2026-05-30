# AgentGuard v1.2.13 Release Prep Validation

Date: 2026-05-30

## Failure Diagnosis

- Publish run `26689523701` reached PyPI upload, so Trusted Publishing no longer failed at the `invalid-publisher` step.
- The run built `agentguard47-1.2.10` artifacts from stale tag `v1.2.12`.
- PyPI rejected the upload because `agentguard47-1.2.10` already exists.
- Recovery path: do not rerun or reuse `v1.2.12`; prepare `v1.2.13` from current `origin/main`.

## Validation

- `python scripts/generate_pypi_readme.py --check`: passed
- `python scripts/sdk_release_guard.py --json`: `[]`
- `python -m pytest sdk/tests/test_ci_guardrails.py sdk/tests/test_pypi_readme_sync.py sdk/tests/test_sdk_release_guard.py -q`: 18 passed
- `python scripts/sdk_preflight.py`: passed
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`: 772 passed, 92.82% coverage
- `python scripts/ci_tools_requirements_guard.py`: passed
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py scripts/ci_tools_requirements_guard.py`: passed
- `python -m pytest sdk/tests/test_architecture.py -v`: 9 passed
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`: passed
- `npm --prefix mcp-server ci`: passed, 0 vulnerabilities
- `npm --prefix mcp-server test`: 10 passed
- `npm --prefix mcp-server run build`: passed
- `python -m pip install -e ./agentguard-mcp && cd agentguard-mcp && python -m ruff check agentguard_mcp tests && python -m pytest`: 15 passed

## Clean Venv Wheel Smoke

See `clean-venv-smoke.log` for the full transcript.

- Built `agentguard47-1.2.13-py3-none-any.whl`.
- Installed with `pip install --no-index --find-links <dist> agentguard47==1.2.13`.
- Import proof:
  - `agentguard.__version__=1.2.13`
  - package metadata `1.2.13`
  - `agentguard.__file__` resolved inside the temporary venv `site-packages`.
- `agentguard doctor`: passed, local-only, no dashboard or network required.
- `agentguard demo`: passed and visibly tripped budget, loop, and retry guards.
- `agentguard quickstart --framework raw --write`: wrote `agentguard_raw_quickstart.py`.
- `python agentguard_raw_quickstart.py`: tripped budget and loop guards.
- `agentguard report .agentguard/traces.jsonl`: reported 14 events, estimated cost `$5.0200`, one budget guard event, and one loop guard event.
