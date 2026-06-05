# SDK State

**Last Updated:** 2026-06-05

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
- distribution before new features
- coding-agent onboarding and proof

## Adoption Reality (verified 2026-06-05)
Do not treat download/clone counts as traction. They are dominated by machines:
- PyPI is ~97% Linux and pypistats already excludes mirrors; **no workflow
  installs the published package** (CI uses `pip install -e ./sdk`), so the
  ~950/month is the external automation ecosystem (cloud CI, Docker, dependency/
  security scanners), not us and not humans.
- GitHub clones (19.3k/14d, 945 unique cloners, ~20x per cloner) are partly our
  own push-heavy CI (>=500 workflow runs/14d) and mostly external scraper bots.
  A 3-star repo does not have 945 human cloners.
- **True human baseline:** 3 stars, 0 external issues/PRs, ~72 unique viewers
  /14d, ~11 referral visits/14d. This is the number to grow.
- Pulse instrument: `make stats` / `scripts/sdk_pulse.py` splits HUMAN SIGNAL
  from MACHINE VOLUME and appends `proof/pulse/history.jsonl` for trend.
