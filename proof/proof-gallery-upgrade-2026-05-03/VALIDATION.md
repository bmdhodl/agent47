# Proof Gallery Upgrade Validation

Date: 2026-05-03
Branch: `codex/proof-gallery-upgrade`

## Goal

Make the public proof gallery more complete and harder to let drift.

## What Changed

- Added a dedicated MCP read-path proof section to
  `docs/examples/proof-gallery.md`.
- Added test coverage that verifies:
  - local `python examples/*.py` references in the proof gallery point to files
    that exist
  - Markdown links in the proof gallery point to files that exist
  - the MCP read-path section keeps the read-only boundary and API-key
    requirement explicit

## Validation

```text
python -m pytest sdk\tests\test_example_starters.py -v
9 passed in 1.20s

npm --prefix mcp-server test
tests 5
pass 5
fail 0

python -m ruff check sdk\tests\test_example_starters.py
All checks passed!

python scripts\sdk_preflight.py
All checks passed!

git diff --check
passed
```

## Risk

Low. This is docs plus sync coverage only. No SDK runtime behavior, MCP runtime
behavior, package metadata, or dependency changes.
