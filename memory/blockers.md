# SDK Blockers

**Last Updated:** 2026-05-30 (release unblocked; `1.2.13` shipped)

## Active
- **Glama tool catalog is not indexed yet.** Patrick published the first Glama
  release on 2026-05-08 and the listing is live. Glama renders tool and score
  pages, but `https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47` still
  returns `tools: []`. Recheck before relying on the API for tool inventory.
- **Glama related servers need manual submission.** `glama.json` only claims
  maintainers. Related servers are added through the Glama UI; use the
  candidates in `docs/launch/distribution-execution.md`.
- **Official MCP Registry metadata is stale (manual publish gated).** npm serves
  `@agentguard47/mcp-server@0.2.2` and `mcp-server/server.json` +
  `mcp-server/package.json` are already at `0.2.2`, but the registry still
  reports `0.2.1` (verified 2026-05-30). The only step left is the credentialed
  publish, which needs the `mcp-publisher` CLI and a GitHub maintainer login
  (not scriptable in CI). Run from `mcp-server/`: `npm publish` (already done
  for 0.2.2), then `mcp-publisher login github` and `mcp-publisher publish`.
- **`awesome-mcp-servers` PR #4012 is CLOSED, not open.** The earlier
  AI-tagged PR (`punkpeye/awesome-mcp-servers#4012`, title "...🤖🤖🤖") was
  closed on 2026-04-04, not merged. Re-listing requires a fresh, guideline-clean
  PR with the Glama URL `https://glama.ai/mcp/servers/bmdhodl/agent47`. Submit
  manually; do not auto-open low-effort PRs against this third-party list.

## Recently Resolved
- **`1.2.13` shipped** to PyPI on 2026-05-30 with a matching GitHub Release
  marked Latest. The release path is no longer blocked.
- **Dead tags `v1.2.11` and `v1.2.12` deleted** from the remote and local on
  2026-05-30 (neither had a PyPI or GitHub Release). Recorded SHAs for recovery
  if ever needed: `v1.2.11` = `3a6d13c`, `v1.2.12` = `8fd0295`.

## Do Not Route Around
- Do not build new guards just because registry indexing lags.
- Do not put business or consulting workaround plans in this repo.
