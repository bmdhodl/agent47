# Dashboard Handoff Guide Validation

## Scope

Docs and package README only. No SDK runtime behavior, public API, telemetry,
dependencies, dashboard code, hosted ingest contract, or MCP package metadata
changed.

Changed:

- `docs/guides/dashboard-contract.md`
- `README.md`
- `sdk/PYPI_README.md`
- `CHANGELOG.md`

## Proof Target

The docs now make the local-to-hosted boundary explicit:

- use local SDK for one-repo proof, hard stops, JSONL traces, local reports, and
  pre-production testing
- use hosted dashboard when multiple people need retained incident history,
  alerts, spend trends, or dashboard-managed remote kill signals
- local safety remains in-process and does not require hosted ingest

## Checks

```text
python scripts\generate_pypi_readme.py --check
passed.

python -m pytest sdk\tests\test_pypi_readme_sync.py -v
4 passed.

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_preflight.py
4 passed through the PyPI README sync test path.

git diff --check
passed.
```
