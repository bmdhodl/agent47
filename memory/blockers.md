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
- **`awesome-mcp-servers` re-list PR is open upstream and out of our hands.**
  Fresh PR `punkpeye/awesome-mcp-servers#7164` (opened 2026-05-31) adds the
  Monitoring entry *with* the Glama score badge that got the old #4012 closed.
  Merge is the upstream maintainers' call. The maintainer bot also wants the
  Glama listing to pass checks, which depends on the Glama tool-indexing item
  above, so watch #7164 for a nudge.

## Recently Resolved
- **MCP Registry now serves `0.2.2`** (`isLatest: true`, published
  2026-05-31T00:08 via the new OIDC `publish-mcp-registry.yml` workflow). The
  manual `mcp-publisher login github` device flow is no longer needed; run
  `gh workflow run publish-mcp-registry.yml` after each npm publish. The
  registry now caps `server.json` descriptions at 100 chars (the first publish
  422'd on a 103-char description; trimmed to 86).
- **`1.2.13` shipped** to PyPI on 2026-05-30 with a matching GitHub Release
  marked Latest. The release path is no longer blocked.
- **Dead tags `v1.2.11` and `v1.2.12` deleted** from the remote and local on
  2026-05-30 (neither had a PyPI or GitHub Release). Recorded SHAs for recovery
  if ever needed: `v1.2.11` = `3a6d13c`, `v1.2.12` = `8fd0295`.

## Do Not Route Around
- Do not build new guards just because registry indexing lags.
- Do not put business or consulting workaround plans in this repo.
