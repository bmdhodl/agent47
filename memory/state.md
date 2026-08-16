# SDK State

**Last Updated:** 2026-08-15

## Product
- AgentGuard = zero-dependency Python SDK for runtime guardrails.
- Focus: runtime enforcement + coding-agent safety.
- SDK stays free, MIT, and local-first.

## Public Artifacts
- PyPI package: `agentguard47` (public latest is `1.2.13`, published
  2026-05-30 with a matching GitHub Release marked Latest)
- Current shipped release: `1.2.13`
- Release candidate under preparation: `1.2.14`; it is not public until the
  release-prep change lands on `main` and the tag workflow publishes it.
- npm MCP package: `@agentguard47/mcp-server@0.2.2` is published.
- Local budget MCP package: `agentguard-mcp` exists in this repo but is not
  published to npm or PyPI; dogfood installs it from the checkout.
- Official MCP Registry listing: live as `io.github.bmdhodl/agentguard47`;
  public search returns both historical `0.2.1` and current `0.2.2`, with
  `0.2.2` marked `isLatest: true`.
- Glama listing: live at `https://glama.ai/mcp/servers/bmdhodl/agent47`.
  The public API still returns the environment schema but an empty `tools`
  array as of 2026-08-15. Treat rendered-listing evidence separately from API
  indexing and do not infer source tool absence from the API response.

## Repo Scope
- `sdk/` = public runtime guardrails SDK
- `mcp-server/` = read-only MCP surface over AgentGuard data
- hosted dashboard remains private and separate

## Current Focus
- `1.2.13` is shipped; the unreleased onboarding bundle on `main` now has a
  clean-wheel activation proof from an isolated venv: module entry point,
  welcome, doctor, demo, raw quickstart generation/execution, report, and badge
  all completed without API keys or network. This is local candidate evidence,
  not public v1.2.13 behavior. The 2026-08-15 baseline is 4 GitHub stars and
  5/18/106 PyPI downloads for the last day/week/month. Downloads are not
  distinct-user or production proof.
- `main` is ahead of `v1.2.13` with unreleased onboarding improvements; the
  next SDK tag must pass the full release gates before those are called public.
- External adoption signal: issue `#686` proposes optional OAA-signed local
  traces. It is one substantive user request, not repeat adoption proof; the
  referenced OAA project is still a draft with no adopters, so implementation
  remains deferred pending spec maturity or an interoperability PR.
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
