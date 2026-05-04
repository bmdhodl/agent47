# PR Draft

## Title
Add local-first agentguard-mcp budget server

## Summary
- add a new `agentguard-mcp` Python package that exposes MCP tools for local token and dollar budgets
- persist budget definitions and usage events in SQLite with session/day/month read-time rollover
- add kill-switch handling, matching scope accounting, and an opt-in non-blocking sync hook
- add a thin `agentguard-mcp` npm shim plus Claude Desktop, Claude Code, Cursor, and Cline setup docs
- save local proof for budget set, call recorded, budget exceeded, and kill-switch blocked behavior

## Scope
- `agentguard-mcp/`
- `npm/agentguard-mcp/`
- `examples/agentguard-mcp/`
- `proof/agentguard-mcp/`
- `Makefile`

## Non-goals
- no hosted dashboard
- no Stripe, billing, accounts, or multi-tenant sync server
- no web UI
- no Slack or email alerts
- no changes to the existing read-only `mcp-server/` behavior
- no new dependency in the zero-dependency core SDK

## Risk
- medium: this adds a new publishable package surface and one new runtime dependency on the official `mcp` SDK inside that package only
- core SDK behavior is unchanged
- existing TypeScript MCP behavior is unchanged
- rollback is a straight revert of the new package, npm shim, examples, proof, and Makefile target

## Validation
- `python -m pip install -e .\agentguard-mcp`
- `cd agentguard-mcp && python -m pytest`
- `cd agentguard-mcp && python -m ruff check agentguard_mcp tests`
- `python -c "import agentguard_mcp.server as s; print('tools', sorted(['set_budget','check_remaining','record_call','kill_switch','list_budgets']))"`
- `npm --prefix mcp-server ci`
- `npm --prefix mcp-server test`
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py`
- `python -m pytest sdk/tests/test_architecture.py -v`
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- `python scripts/sdk_preflight.py`
- `python -m build .\agentguard-mcp`
- `cd npm/agentguard-mcp && npm pack --dry-run`

`make` is unavailable in this Windows shell, so Makefile-equivalent commands
were run directly. Proof is saved in `proof/agentguard-mcp/local-budget-proof.txt`.

## Screenshots / Proof
- Local terminal proof: `proof/agentguard-mcp/local-budget-proof.txt`
- Claude Desktop screenshots are still needed from Patrick's configured desktop client before publishing.
