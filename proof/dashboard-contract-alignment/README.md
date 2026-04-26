# Dashboard Contract Alignment Proof

Date: 2026-04-25

## Commands

- `make check`
  - Result: unavailable in this Windows shell; see `make-check.txt`.
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py`
  - Result: pass; see `ruff.txt`.
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
  - Result: `693 passed`, coverage `92.88%`; see `pytest-full.txt`.
- `npm --prefix mcp-server test`
  - Result: pass; see `mcp-test.txt`.
- `python -m pytest sdk/tests/test_architecture.py -v`
  - Result: pass; see `structural.txt`.
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`
  - Result: pass; see `security.txt`.
- `gitleaks detect --source . --redact --no-color --no-banner --exit-code 1`
  - Result: pass; see `gitleaks.txt`.
- `python scripts/sdk_release_guard.py`
  - Result: pass; see `release-guard.txt`.
- `python scripts/sdk_preflight.py`
  - Result: pass; see `preflight.txt`.

## Contract Evidence

- SDK decision helpers now emit non-empty `binding_state` defaults for
  proposed, edited, overridden, and approved events.
- Local ingest tests now report decision-trace warnings for accepted events
  whose decision payload would not be queryable by the dashboard.
- The remote-kill boundary is documented: `HttpSink` mirrors events but does
  not poll or execute kill signals by itself.
