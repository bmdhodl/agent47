# AgentGuard MCP Server

Read-only MCP (Model Context Protocol) server that connects coding agents to
the AgentGuard Read API. Use it after the local SDK is already in place and
you want Codex, Claude Code, Cursor, or another MCP client to inspect traces,
alerts, usage, costs, and budget health.

The boundary is deliberate:
- The SDK proves runtime enforcement locally
- The MCP server gives coding agents a narrow read surface over retained data
- The hosted dashboard stays the operational control plane

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

## Glama / Smithery Build Config

This repo now includes the files downstream registries expect when they build
or inspect the MCP server from GitHub:

- [`Dockerfile`](Dockerfile) - container build for the stdio server
- [`smithery.yaml`](smithery.yaml) - config schema for `AGENTGUARD_API_KEY`
  and the optional base URL

That keeps the public repo aligned with the published npm package and makes the
Glama / Smithery import path explicit instead of implicit.

The repo root also carries matching shim files for directories that only scan
the default branch root:

- [`../Dockerfile`](../Dockerfile)
- [`../smithery.yaml`](../smithery.yaml)

Those root files delegate straight to `mcp-server/` and should stay aligned
with the package-local versions here.

## Registry Readiness

This repo now includes official MCP registry metadata in
[`server.json`](server.json). The npm package is already public, and the Glama /
Smithery config now lives next to the source, so the remaining registry work is
metadata publication:

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
