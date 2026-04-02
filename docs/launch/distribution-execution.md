# Distribution Execution

This is the shortest path from "repo is ready" to "AgentGuard is in front of
real coding-agent users."

## Order of Operations

1. Official MCP Registry
2. Glama
3. `awesome-mcp-servers`
4. Show HN
5. LangChain Forum / GitHub Discussions
6. Codex open source fund

## 1. Official MCP Registry

Package and metadata are prepared in this repo:
- npm package: `@agentguard47/mcp-server`
- registry name: `io.github.bmdhodl/agentguard47`
- metadata file: [`mcp-server/server.json`](../../mcp-server/server.json)

Manual steps:

```bash
cd mcp-server
npm publish
mcp-publisher login github
mcp-publisher publish
```

Important:
- publish the npm package first whenever `package.json` metadata changes
- the MCP registry validates the live npm tarball, not just your local working tree
- `package.json:mcpName` must match `server.json:name`

Verify:

```bash
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.bmdhodl/agentguard47"
```

## 2. Glama

Listing details to reuse:
- Name: `AgentGuard`
- One-liner: `MCP server for coding-agent traces, alerts, costs, usage, and budget health`
- npm package: `@agentguard47/mcp-server`
- Repo: `https://github.com/bmdhodl/agent47`
- MCP metadata name: `io.github.bmdhodl/agentguard47`

Use the same description and install command as `mcp-server/server.json`.
This repo now also ships:
- [`mcp-server/Dockerfile`](../../mcp-server/Dockerfile)
- [`mcp-server/smithery.yaml`](../../mcp-server/smithery.yaml)

Those files make the Glama / Smithery build path explicit and document the
required `AGENTGUARD_API_KEY` configuration for directory checks.

## 3. awesome-mcp-servers

Open a PR against the upstream list with:
- project name: `AgentGuard`
- category: monitoring / devtools / safety
- short description: `Runtime guardrails and read access for coding-agent traces, alerts, and budget health`
- install target: `npx -y @agentguard47/mcp-server`

## 4. Show HN

Use [`show-hn.md`](show-hn.md) as the source of truth.

Required assets before posting:
- one short terminal/GIF clip
- one screenshot of the smoke flow
- one screenshot of the README hero

## 5. LangChain Forum / GitHub Discussions

Use the community angle:
- loops
- retry storms
- runaway spend
- coding-agent safety

Do not lead with pricing or generic observability.

## 6. Codex Open Source Fund

Apply here:
- [Codex open source fund](https://openai.com/form/codex-open-source-fund/)

Use these points:
- 6,400+ organic PyPI downloads
- zero-dependency MIT SDK
- focused on coding-agent safety
- clear local-first proof with `doctor`, `demo`, `quickstart`, and smoke test

## Message to Repeat Everywhere

> AgentGuard stops coding agents from looping, retrying forever, and burning budget.

Support points:
- zero dependency
- local first
- safe to try
- works before dashboard signup
- hosted dashboard comes later for alerts and retained history
