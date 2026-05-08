# Release Guard Hardening Validation

## Scope

Release infrastructure only. No Python SDK runtime behavior, public API,
dashboard code, hosted ingest contract, MCP runtime behavior, or dependencies
changed.

Changed:

- `scripts/sdk_release_guard.py`
- `sdk/tests/test_sdk_release_guard.py`
- `CHANGELOG.md`

## What Changed

Added `python scripts/sdk_release_guard.py --check-mcp-npm`.

The default release guard remains network-free. The optional flag verifies that:

- `mcp-server/package.json` has a package name and version
- `npm view <package>@<version> version` succeeds
- `npm view <package> version` matches the repo package version

## Current Live Result

```text
python scripts\sdk_release_guard.py --check-mcp-npm
Release guard passed.
```

`@agentguard47/mcp-server@0.2.2` is now published on npm and matches npm
latest.

## Checks

```text
python -m pytest sdk\tests\test_sdk_release_guard.py -v
10 passed.

python -m ruff check scripts\sdk_release_guard.py sdk\tests\test_sdk_release_guard.py
All checks passed.

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_release_guard.py --check-mcp-npm
Release guard passed.

python scripts\sdk_preflight.py
All checks passed.

git diff --check
passed.
```
