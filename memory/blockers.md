# SDK Blockers

**Last Updated:** 2026-05-30 (release unblocked; `1.2.13` shipped)

## Active
- **`awesome-mcp-servers` re-list PR is open upstream and out of our hands.**
  Fresh PR `punkpeye/awesome-mcp-servers#7164` (opened 2026-05-31) adds the
  Monitoring entry *with* the Glama score badge that got the old #4012 closed.
  The Glama listing now passes checks (all 7 tools indexed, graded A), so the
  bot's requirements are met; merge is the upstream maintainers' call.
- **Glama "no recent usage" is the only open listing item (needs the read key).**
  Glama profile completion is 92%; the lone remaining checklist warning is "no
  recent usage". Seed it via the listing's "Try in Browser" with a real
  `AGENTGUARD_API_KEY`, or let real traffic clear it. Do not commit the key.

## Recently Resolved
- **Glama tool catalog is indexed and graded.** All 7 tools (`query_traces`,
  `get_trace`, `get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`,
  `check_budget`) show on the Schema tab, each graded A; license/quality/
  maintenance are all A. The old `tools: []` was a stale public-API cache, not a
  real gap. The `1.2.13` build test passes.
- **Glama related servers added** (2026-05-31) via the UI: `getsentry/sentry-mcp`,
  `therealsachin/langfuse-mcp-server`, `agarwalvivek29/opentelemetry-mcp`. The
  "no related servers" checklist item is cleared.
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
