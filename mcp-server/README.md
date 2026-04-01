# AgentGuard MCP Server

MCP (Model Context Protocol) server that connects coding agents to the
AgentGuard Read API. It lets agents inspect their own traces, alerts, usage,
costs, and saved spend after the local SDK is already in place.

The boundary is deliberate:
- A.SDK proves runtime enforcement locally
- the MCP server gives coding agents a narrow read surface over retained data
- the hosted dashboard stays the operational control plane

## Published Package

```bash
npx -y @agentguard47/mcp-server
```

## Tools

| Tool | Description |
|------|-------------|
| `query_traces` | Search recent traces, filter by service/time range |
| `get_trace` | Get the full event tree for a specific trace ID |
| `get_alerts` | Get guard alerts such as loops, budget exceeded, and errors |
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
      "command": "npx",
      "args": ["-y", "@agentguard47/mcp-server"],
      "env": {
        "AGENTGUARD_API_KEY": "ag_your_key_here"
      }
    }
  }
}
```

Any other MCP-compatible client that can launch an npm package over stdio can
use the same command.

## Local Build & Run

```bash
npm ci
npm run build
npm start
```

## Registry Readiness

This repo now includes official MCP registry metadata in
[`server.json`](server.json). The npm package is already public, so the
remaining registry work is metadata publication:

```bash
mcp-publisher login github
mcp-publisher publish
```

After that, verify the server is searchable from the MCP Registry API and then
submit it to downstream directories like Glama and `awesome-mcp-servers`.

## Architecture

- `src/index.ts` - Server entry point, tool registration (stdio transport)
- `src/client.ts` - HTTP client wrapping `/api/v1/` endpoints
- `src/tools.ts` - 6 MCP tool definitions and handlers
