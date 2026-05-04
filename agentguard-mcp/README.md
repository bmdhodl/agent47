# agentguard-mcp

`agentguard-mcp` is a local MCP server for budgets. It lets MCP clients record tool calls, track token and dollar spend, and block calls when a per-tool, per-server, per-session, or per-day budget is exceeded. State lives in SQLite on your machine. No account. No telemetry. No network call unless you opt into `AGENTGUARD_SYNC_URL`.

This is the MCP-native sibling of [`agentguard47`](https://pypi.org/project/agentguard47/). Use `agentguard47` when you want guards inside Python agent code. Use `agentguard-mcp` when you want one local server that MCP-compatible tools can call.

## Install

```bash
pip install agentguard-mcp
```

Or run through npm:

```bash
npx -y agentguard-mcp
```

By default, local state is stored at `~/.agentguard/state.db`. Set `AGENTGUARD_DB_PATH` to use a different SQLite file.

## Claude Desktop

```json
{
  "mcpServers": {
    "agentguard-mcp": {
      "command": "agentguard-mcp",
      "args": [],
      "env": {
        "AGENTGUARD_DB_PATH": "~/.agentguard/state.db"
      }
    }
  }
}
```

## Claude Code

```bash
claude mcp add agentguard-mcp -- agentguard-mcp
```

## Cursor

```json
{
  "mcpServers": {
    "agentguard-mcp": {
      "command": "npx",
      "args": ["-y", "agentguard-mcp"]
    }
  }
}
```

## Cline

```json
{
  "mcpServers": {
    "agentguard-mcp": {
      "command": "agentguard-mcp",
      "args": []
    }
  }
}
```

## Quickstart

Set a $5/day global budget:

```json
{
  "scope": "global",
  "limit_tokens": null,
  "limit_usd": 5.0,
  "period": "day"
}
```

Record one heavy call:

```json
{
  "server": "github",
  "tool": "create_issue",
  "tokens_in": 90000,
  "tokens_out": 20000,
  "cost_usd": 6.25,
  "session_id": "demo"
}
```

The `record_call` tool returns:

```json
{
  "allowed": false,
  "reasons": ["global dollar budget exceeded: 6.250000 > 5.000000"],
  "scopes_checked": ["global", "server:github", "tool:github.create_issue", "session:demo"]
}
```

## Tools

- `set_budget(scope, limit_tokens, limit_usd, period)` sets a budget. `period` is `session`, `day`, or `month`.
- `check_remaining(scope)` returns current usage, limits, and reset time.
- `record_call(server, tool, tokens_in, tokens_out, cost_usd, session_id)` records usage against `global`, `server:<server>`, `tool:<server>.<tool>`, and `session:<id>`.
- `kill_switch(scope, enable)` blocks matching calls before usage is recorded.
- `list_budgets()` returns configured budgets with current usage.

## Optional sync

Set `AGENTGUARD_SYNC_URL` to POST every `record_call` event to another system. Set `AGENTGUARD_SYNC_TOKEN` to send `Authorization: Bearer <token>`. Sync runs in a background thread with a 2 second timeout and never blocks the MCP response.

Hosted history, alerts, and team controls are available at [bmdpat.com/tools/agentguard](https://bmdpat.com/tools/agentguard).
