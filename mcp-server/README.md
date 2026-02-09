# AgentGuard MCP Server

MCP (Model Context Protocol) server that connects AI coding agents to the AgentGuard Read API. Lets agents query their own traces, alerts, costs, and budget status.

## Tools

| Tool | Description |
|------|-------------|
| `query_traces` | Search recent traces, filter by service/time range |
| `get_trace` | Get full event tree for a specific trace ID |
| `get_alerts` | Get guard alerts (loops, budget exceeded, errors) |
| `get_usage` | Check event quota usage and plan limits |
| `get_costs` | Get cost breakdown by model for the current month |
| `check_budget` | Quick pass/fail budget health check |

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENTGUARD_API_KEY` | Yes | Bearer token for the Read API (`ag_...`) |
| `AGENTGUARD_URL` | No | API base URL (defaults to production) |

## Setup for Claude Code

Add to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "agentguard": {
      "command": "node",
      "args": ["/path/to/agent47/mcp-server/dist/index.js"],
      "env": {
        "AGENTGUARD_API_KEY": "ag_your_key_here"
      }
    }
  }
}
```

## Build & Run

```bash
npm ci          # Install dependencies
npm run build   # Compile TypeScript
npm start       # Run server (stdio transport)
npm run dev     # Watch mode for development
```

## Architecture

- `src/index.ts` — Server entry point, tool registration (stdio transport)
- `src/client.ts` — HTTP client wrapping `/api/v1/` endpoints
- `src/tools.ts` — 6 MCP tool definitions and handlers
