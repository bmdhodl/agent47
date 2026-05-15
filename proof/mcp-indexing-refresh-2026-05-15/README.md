# MCP Indexing Refresh — 2026-05-15

Maintenance / distribution hygiene check for `@agentguard47/mcp-server`. No SDK
or MCP runtime code change. Source task:
`Queue/agent47/2026-05-09-refresh-agentguard-mcp-indexing.md`.

## Repo state

- `mcp-server/package.json` version: `0.2.2`
- `mcp-server/server.json` version: `0.2.2`

## Live state (verified 2026-05-15)

### npm

- Latest: `0.2.2` (versions: `0.1.0`, `0.2.0`, `0.2.1`, `0.2.2`)
- Modified: `2026-05-04T19:38:49.604Z`
- URL: https://www.npmjs.com/package/@agentguard47/mcp-server
- API: https://registry.npmjs.org/@agentguard47/mcp-server
- Status: matches repo. No action.

### Official MCP Registry

- Name: `io.github.bmdhodl/agentguard47`
- Reported version: `0.2.1`
- `statusChangedAt` / `updatedAt`: `2026-04-02T16:27:26.234163Z`
- `isLatest`: `true` (but version lags npm)
- URL: https://registry.modelcontextprotocol.io/v0/servers?search=agentguard47
- Status: STALE. Registry still reports `0.2.1`. Needs a registry republish to
  reflect npm `0.2.2`.

### Glama

- ID: `y6zuc6wgtu`, slug: `bmdhodl/agent47`
- URL: https://glama.ai/mcp/servers/bmdhodl/agent47
- API: https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47
- Environment schema: present and current
- `tools`: `[]` (empty)
- Status: STALE. The seven expected tools are not exposed via Glama's public
  API:
  - `query_traces`
  - `get_trace`
  - `get_trace_decisions`
  - `get_alerts`
  - `get_usage`
  - `get_costs`
  - `check_budget`

## Tool names verified in `mcp-server/src/tools.ts`

All seven tools are present in source (lines 19, 73, 90, 112, 132, 149, 163).
No code drift.

## Blockers

Both registry refresh and Glama re-indexing require external credentials /
manual action and are NOT scripted in this repo (no `mcp-publisher`,
`glama-cli`, or registry/Glama scripts under `scripts/`).

### Blocker 1 — MCP Registry republish

- **What it needs:** `mcp-publisher` CLI authenticated as the
  `io.github.bmdhodl` maintainer, run against `mcp-server/server.json`.
- **Why the worker cannot do it autonomously:** the publisher CLI is not
  installed in this environment and would require maintainer credentials that
  must not be auto-fetched. The repo docs
  (`docs/release/mcp-publishing.md`) describe the publish step as a manual
  operation gated on an OTP.
- **Resume path:** Patrick (or a Patrick-credentialed session) runs
  `mcp-publisher publish` against `mcp-server/server.json` from a logged-in
  shell. After publish, re-curl the registry search endpoint and confirm
  version `0.2.2`.

### Blocker 2 — Glama tool catalog indexing

- **What it needs:** manual action in Glama's UI to trigger a re-scan of the
  server's tool list, OR contact Glama support to refresh the index.
- **Why the worker cannot do it autonomously:** Glama's public API does not
  expose an admin re-index endpoint. The repo's existing
  `memory/distribution.md` already flagged this as needing manual UI work.
- **Resume path:** sign in to Glama as `bmdhodl`, trigger a tool list refresh
  on the server page. After refresh, re-curl
  `https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47` and confirm `tools`
  contains the seven names listed above.

## Files changed in this PR

- `memory/distribution.md` — updated channel state with verified live numbers,
  links, and a precise description of each blocker. Replaces the earlier
  "metadata refresh needed" / "public API tool catalog still lags" phrasing.

No code change. No `mcp-server/` change. No SDK change. No dashboard change.
No new dependency.
