# Follow-up

- Recheck the Glama rendered listing and the "no recent usage" checklist item
  with the read key. The public API still returned `tools: []` on 2026-08-15;
  do not change SDK or MCP runtime code solely to chase that directory signal.
- Keep the official MCP Registry readback in the weekly MCP train. It currently
  serves `0.2.2` as `isLatest: true`; the older `0.2.1` result is expected
  historical metadata.
- Record explicit external adoption evidence from three repeat users or design
  partners before broadening the SDK feature surface. Use issues, PRs, or
  user-provided proof; do not add telemetry to manufacture this signal.
- Harden `agentguard-mcp/agentguard_mcp/sync.py`: `SyncHook` POSTs to
  `AGENTGUARD_SYNC_URL` with no scheme/host validation, unlike `HttpSink`
  (which blocks private/reserved IPs and non-http(s) schemes). It is an opt-in
  operator env var, so low risk, but add minimal scheme validation
  (reject non-http(s)) + a test so the consistency gap does not reappear.
  Found during the 2026-06-06 QA pass (see `proof/qa-2026-06-06/REPORT.md`).
