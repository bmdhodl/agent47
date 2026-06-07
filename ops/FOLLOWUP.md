# Follow-up

- Verify Glama tool indexing after the first release. The listing is live and
  rendered tool/score pages exist, but the public API still returned `tools: []`
  on 2026-05-08.
- Submit related servers in Glama UI: Langfuse MCP, OpenTelemetry MCP, and
  Sentry MCP are the closest monitoring / trace / incident neighbors.
- Refresh official MCP Registry metadata so public search reports
  `@agentguard47/mcp-server@0.2.2` instead of `0.2.1`.
- Comment `https://glama.ai/mcp/servers/bmdhodl/agent47` on
  `punkpeye/awesome-mcp-servers#4012` once the Glama listing is acceptable for
  the badge requirement.
- Harden `agentguard-mcp/agentguard_mcp/sync.py`: `SyncHook` POSTs to
  `AGENTGUARD_SYNC_URL` with no scheme/host validation, unlike `HttpSink`
  (which blocks private/reserved IPs and non-http(s) schemes). It is an opt-in
  operator env var, so low risk, but add minimal scheme validation
  (reject non-http(s)) + a test so the consistency gap does not reappear.
  Found during the 2026-06-06 QA pass (see `proof/qa-2026-06-06/REPORT.md`).
