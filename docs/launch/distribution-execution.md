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

Current listing:
- URL: `https://glama.ai/mcp/servers/bmdhodl/agent47`
- Namespace / slug: `bmdhodl/agent47`
- Status: first release published on 2026-05-08. Glama API shows the
  environment schema but still returns an empty `tools` array, so recheck before
  treating the directory listing as fully indexed.

Listing details:
- Name: `AgentGuard`
- One-liner: `Runtime safety infrastructure for AI agents`
- Description: `AgentGuard47 is runtime safety infrastructure for AI agents. It adds budget caps, loop detection, retry limits, timeouts, local traces, and incident reports so agents can stop bad runs while they are happening, not just explain them afterward.`
- npm package: `@agentguard47/mcp-server`
- Repo: `https://github.com/bmdhodl/agent47`
- MCP metadata name: `io.github.bmdhodl/agentguard47`

This repo now also ships:
- [`mcp-server/Dockerfile`](../../mcp-server/Dockerfile)
- [`mcp-server/smithery.yaml`](../../mcp-server/smithery.yaml)

Those files make the Glama / Smithery build path explicit and document the
required `AGENTGUARD_API_KEY` configuration for directory checks.

Important:
- Glama currently scans the repository root when detecting Smithery metadata
- this repo therefore ships a root-level [`Dockerfile`](../../Dockerfile) and
  [`smithery.yaml`](../../smithery.yaml) that delegate to `mcp-server/`
- keep the root shim aligned with the real package-local files in
  [`mcp-server/`](../../mcp-server/)

Release procedure used for `0.2.2`:

1. Open `https://glama.ai/mcp/servers/bmdhodl/agent47/admin/dockerfile`.
2. Use the repository root Dockerfile. It builds `mcp-server/` and runs
   `node /app/mcp-server/dist/index.js`.
3. Configure environment variables:

   | Variable | Required | Secret | Default | Description |
   |---|---:|---:|---|---|
   | `AGENTGUARD_API_KEY` | Yes | Yes | | AgentGuard read API key for traces, alerts, costs, usage, and budget health |
   | `AGENTGUARD_URL` | No | No | `https://app.agentguard47.com` | Optional AgentGuard API base URL |

4. Deploy the build test.
5. After the test passes, create and publish the Glama release with version
   `0.2.2` and changelog `Initial Glama release for AgentGuard MCP server.`

After release, verify the public API exposes the environment schema and the 7
tools:

```bash
curl "https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47"
```

Expected tools once indexing completes: `query_traces`, `get_trace`,
`get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`, `check_budget`.

## 3. awesome-mcp-servers

Open a PR against the upstream list with:
- project name: `AgentGuard`
- category: monitoring / devtools / safety
- short description: `Runtime guardrails and read access for coding-agent traces, alerts, and budget health`
- install target: `npx -y @agentguard47/mcp-server`
- Glama URL: `https://glama.ai/mcp/servers/bmdhodl/agent47`

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
