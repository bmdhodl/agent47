# SDK Distribution

**Last Updated:** 2026-08-15

## Core Message
AgentGuard stops coding agents from looping, retrying forever, and burning
budget before the next bad call lands.

## Audience
- developers using coding agents
- small teams shipping AI agents
- teams worried about runaway spend and unsafe automation

## Channels
- npm `@agentguard47/mcp-server`: latest `0.2.2`, modified 2026-05-04; matches
  `mcp-server/package.json` and `mcp-server/server.json`
- Official MCP Registry: live as `io.github.bmdhodl/agentguard47`; public API
  serves current `0.2.2` (`isLatest: true`, published 2026-05-31) alongside
  historical `0.2.1`. Republish is scripted via the OIDC
  `publish-mcp-registry.yml` workflow
  (`gh workflow run publish-mcp-registry.yml`); no manual `mcp-publisher` login
- Glama: live at `https://glama.ai/mcp/servers/bmdhodl/agent47` (id
  `y6zuc6wgtu`). The public API returned an empty `tools` array on 2026-08-15;
  retain the rendered-listing notes separately and do not treat the API as
  source inventory. The remaining profile item is "no recent usage" (seed via
  "Try in Browser" with the read key).
- `awesome-mcp-servers`: re-list PR `punkpeye/awesome-mcp-servers#7164` merged
  on 2026-06-06 with the Monitoring entry and Glama URL.
- Show HN
- LangChain / GitHub community posts

## Network-Effect Surfaces
- "Guarded by AgentGuard" README badge via `agentguard badge` (markdown/rst/
  html). Every adopting repo becomes a backlink + social proof. This is the
  direct lever on the stars-vs-downloads gap; promote it wherever a user has
  just seen a guard fire (demo close, report, README).
- Star CTA stays in `doctor`, `demo`, and the bare-command welcome.

## Keep Repeating
- zero dependency
- local first
- safe to try
- runtime guardrails
- coding-agent safety
