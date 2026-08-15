# SDK Blockers

**Last Updated:** 2026-08-15 (release unblocked; `1.2.13` shipped)

## Active
- **Glama listing/API reconciliation remains open (needs the read key).**
  The rendered listing had previously reported the seven tools and a 92%
  profile, but the public API returned an empty `tools` array on 2026-08-15.
  The remaining profile checklist item is "no recent usage". Seed usage via
  the listing's "Try in Browser" with a real `AGENTGUARD_API_KEY`, or let real
  traffic clear it. Do not commit the key.

## Recently Resolved
- **Glama rendered tool catalog was indexed and graded on 2026-05-31.** All 7
  tools (`query_traces`,
  `get_trace`, `get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`,
  `check_budget`) show on the Schema tab, each graded A; license/quality/
  maintenance are all A. The current public API disagrees and is tracked above;
  the `1.2.13` build test passes.
- **Glama related servers added** (2026-05-31) via the UI: `getsentry/sentry-mcp`,
  `therealsachin/langfuse-mcp-server`, `agarwalvivek29/opentelemetry-mcp`. The
  "no related servers" checklist item is cleared.
- **`awesome-mcp-servers` re-list merged.** Upstream PR
  `punkpeye/awesome-mcp-servers#7164` merged on 2026-06-06 with the Monitoring
  entry and Glama URL.
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
