# Morning Report

## Mission
Ship a draftable `agentguard-mcp` package: a local-first MCP server that tracks
per-tool, per-server, per-session, and global budgets in tokens and dollars.

## What changed
- Added `agentguard-mcp/`, a Python package using the official `mcp` SDK with
  FastMCP tools: `set_budget`, `check_remaining`, `record_call`, `kill_switch`,
  and `list_budgets`.
- Added SQLite persistence at `~/.agentguard/state.db`, overridable with
  `AGENTGUARD_DB_PATH`.
- Added read-time period rollover for `session`, `day`, and `month`.
- Added an opt-in `AGENTGUARD_SYNC_URL` hook that POSTs usage events in a
  background thread with a 2 second timeout.
- Added a thin npm shim package at `npm/agentguard-mcp/`.
- Added install/config docs and Claude Desktop, Cursor, and Cline examples.
- Added proof at `proof/agentguard-mcp/local-budget-proof.txt`.

## What is left
- Publish `agentguard-mcp` to PyPI.
- Publish the unscoped npm shim as `agentguard-mcp`.
- Capture Claude Desktop screenshots from a real configured client.
- Open registry PRs/listings for mcp.so, Smithery, Glama, PulseMCP, and
  `awesome-mcp-servers`.

## Validation
- New package tests passed: 6 passed.
- New package ruff passed.
- Existing TypeScript MCP tests passed after `npm --prefix mcp-server ci`.
- SDK ruff passed.
- Full SDK pytest with coverage passed: 709 passed, 93.02% coverage.
- Structural tests passed: 9 passed.
- Bandit passed via `python -m bandit`.
- Release guard passed.
- Python package build passed.
- npm shim dry-run pack passed.
- `make` is unavailable in this Windows shell, so direct equivalents were run.

## Unknowns for Patrick
- Whether to keep the new package as a subdirectory publish or split it into a
  dedicated repo after the draft PR.
- Whether the npm shim should auto-install/upgrade the Python package on every
  run or only on first run.
