# SDK Distribution

**Last Updated:** 2026-05-30

## Core Message
AgentGuard stops coding agents from looping, retrying forever, and burning
budget.

## Audience
- developers using coding agents
- small teams shipping AI agents
- teams worried about runaway spend and unsafe automation

## Channels
- PyPI `agentguard47`: latest `1.2.13`, with GitHub Release `v1.2.13`
  published on 2026-05-30
- npm `@agentguard47/mcp-server`: latest `0.2.2`, modified 2026-05-04; matches
  `mcp-server/package.json` and `mcp-server/server.json`
- Official MCP Registry: live as `io.github.bmdhodl/agentguard47`; public API
  still reports `0.2.1` (statusChangedAt 2026-04-02). Republish requires
  `mcp-publisher` CLI with maintainer credentials and is NOT scripted in this
  repo; see `docs/release/mcp-publishing.md`
- Glama: live at `https://glama.ai/mcp/servers/bmdhodl/agent47` (id
  `y6zuc6wgtu`). Environment schema present; public API `tools: []` still
  empty, so the seven expected tools (`query_traces`, `get_trace`,
  `get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`,
  `check_budget`) are not yet indexed. Requires manual Glama UI action; no
  repo automation
- `awesome-mcp-servers`: next distribution step after Glama listing/tool
  indexing is acceptable for badge/commenting
- Show HN
- LangChain / GitHub community posts

## Keep Repeating
- zero dependency
- local first
- safe to try
- runtime guardrails
- coding-agent safety
