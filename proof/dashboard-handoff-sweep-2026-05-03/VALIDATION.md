# Dashboard Handoff Sweep Validation

Date: 2026-05-03
Branch: `codex/dashboard-handoff-sweep`

## Goal

Keep the SDK-to-dashboard handoff explicit, useful, and non-pushy.

## What Changed

- Tightened README hosted-dashboard wording around:
  - retained history
  - alerts
  - team visibility
  - spend trends
  - hosted decision history
  - dashboard-managed remote kill signals
- Updated `docs/guides/dashboard-contract.md` to use the same language and to
  state that hosted ingest is not required for local safety.
- Regenerated `sdk/PYPI_README.md` from README.
- Added docs guard tests so the boundary does not silently drift.

## Validation

```text
python -m pytest sdk\tests\test_dashboard_handoff_docs.py sdk\tests\test_pypi_readme_sync.py -v
6 passed in 0.08s

python -m ruff check sdk\tests\test_dashboard_handoff_docs.py
All checks passed!

python scripts\generate_pypi_readme.py --check
passed

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_preflight.py
All checks passed!

git diff --check
passed
```

## Risk

Low. This is documentation and docs-test coverage only. No SDK runtime behavior,
MCP runtime behavior, package metadata, or dependency changes.
