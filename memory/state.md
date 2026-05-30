# SDK State

**Last Updated:** 2026-05-30

## Product
- AgentGuard = zero-dependency Python SDK for runtime guardrails.
- Focus: runtime enforcement + coding-agent safety.
- SDK stays free, MIT, and local-first.

## Public Artifacts
- PyPI package: `agentguard47@1.2.13` is public.
- Latest GitHub Release: `v1.2.13`
- npm MCP package: `@agentguard47/mcp-server@0.2.2` is published.
- Local budget MCP package: `agentguard-mcp` exists in this repo but is not
  published to npm or PyPI; dogfood installs it from the checkout.
- Official MCP Registry listing: live as `io.github.bmdhodl/agentguard47`;
  public registry search still reports package version `0.2.1` and needs a
  metadata refresh / republish check.
- Glama listing: live at `https://glama.ai/mcp/servers/bmdhodl/agent47`.
  First Glama release is published; Glama API shows the environment schema, but
  still returns an empty `tools` array as of 2026-05-08.

## Repo Scope
- `sdk/` = public runtime guardrails SDK
- `mcp-server/` = read-only MCP surface over AgentGuard data
- hosted dashboard remains private and separate

## Current Focus
- post-`v1.2.13` distribution health and adoption proof
- distribution before new features
- coding-agent onboarding and proof
