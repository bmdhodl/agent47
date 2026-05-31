# SDK Distribution

**Last Updated:** 2026-05-29

## Core Message
AgentGuard stops coding agents from looping, retrying forever, and burning
budget.

## Audience
- developers using coding agents
- small teams shipping AI agents
- teams worried about runaway spend and unsafe automation

## Channels
- npm `@agentguard47/mcp-server`: latest `0.2.2`, modified 2026-05-04; matches
  `mcp-server/package.json` and `mcp-server/server.json`
- Official MCP Registry: live as `io.github.bmdhodl/agentguard47`; public API
  serves `0.2.2` (`isLatest: true`, published 2026-05-31). Republish is now
  scripted via the OIDC `publish-mcp-registry.yml` workflow
  (`gh workflow run publish-mcp-registry.yml`); no manual `mcp-publisher` login
- Glama: live at `https://glama.ai/mcp/servers/bmdhodl/agent47` (id
  `y6zuc6wgtu`). All seven tools (`query_traces`, `get_trace`,
  `get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`,
  `check_budget`) are indexed and graded A on the Schema tab;
  license/quality/maintenance all A; profile completion 92%; three related
  servers added (sentry, langfuse, opentelemetry). The earlier `tools: []` was
  a public-API cache lag, not a real gap. Only "no recent usage" remains (seed
  via "Try in Browser" with the read key)
- `awesome-mcp-servers`: re-list PR `punkpeye/awesome-mcp-servers#7164` is open
  (2026-05-31) with the Glama score badge the closed #4012 lacked; the Glama
  listing now passes checks, so merge is the upstream maintainers' call
- Show HN
- LangChain / GitHub community posts

## Keep Repeating
- zero dependency
- local first
- safe to try
- runtime guardrails
- coding-agent safety
