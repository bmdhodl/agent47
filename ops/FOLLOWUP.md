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
- Done 2026-08-15: built the current SDK candidate wheel and installed it into
  an isolated venv. `python -m agentguard`, `doctor`, `demo`, raw
  `quickstart --write`, generated-starter execution, `report`, and `badge` all
  completed without API keys or network. This is release-prep evidence only;
  the onboarding bundle remains unreleased until a new SDK tag is published.
- Done 2026-08-15: `agentguard-mcp/agentguard_mcp/sync.py` validates opt-in
  `AGENTGUARD_SYNC_URL` values for an `http`/`https` scheme and hostname before
  starting the background executor. Private destinations remain allowed because
  this is an explicitly configured local hook; broad SSRF blocking remains a
  separate compatibility decision. Tests cover rejected schemes, missing hosts,
  and valid local HTTP URLs.
