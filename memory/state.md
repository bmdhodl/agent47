# SDK State

**Last Updated:** 2026-06-06

## Product
- AgentGuard = zero-dependency Python SDK for runtime guardrails.
- Focus: runtime enforcement + coding-agent safety.
- SDK stays free, MIT, and local-first.

## Public Artifacts
- PyPI package: `agentguard47` (public latest is `1.2.13`, published
  2026-05-30 with a matching GitHub Release marked Latest)
- Current shipped release: `1.2.13`
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
- `1.2.13` is shipped; next push is converting installs into visible proof
  (GitHub stars sit at 3 against thousands of PyPI downloads)
- distribution before new features
- coding-agent onboarding and proof

## Install / Activation Surface (unreleased, on `main`)
- Bare `agentguard` prints a guided first-run welcome (60-second local path +
  star CTA), not an argparse help dump. Logic in `first_run.render_welcome`.
- `python -m agentguard` now works (`sdk/agentguard/__main__.py`) so the CLI
  runs without the console script on PATH. The older `python -m agentguard.cli`
  fallback still works and stays in doctor/demo/quickstart hints.
- `agentguard badge` prints a paste-able "Guarded by AgentGuard" README badge
  (markdown/rst/html) — the cheapest install→backlink network-effect surface,
  aimed directly at the stars-vs-downloads gap. Surfaced in the welcome, the
  demo close, and the README.
