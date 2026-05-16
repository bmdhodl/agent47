# WORK_PLAN — MCP tool-call audit-log primitive

## Problem statement

AgentGuard has no first-class way to record MCP (Model Context Protocol) tool-call
decisions to a durable, parseable log. The queue task asks for a NARROW, audit-only
primitive: a helper that writes one JSONL row per MCP tool call with timestamp,
server, tool, payload digest, decision label, reason, and agent id. This is an
observability extension of the existing decision/audit surface — NOT a policy
engine, allowlist/denylist, PHI regex bundle, rate limiter, or governance product.

## Approach

Add a new stdlib-only core module `agentguard/mcp_audit.py` exposing:

- `digest_payload(payload, *, algorithm="sha256") -> str` — deterministic hex digest
  of a JSON-canonicalized tool-call payload. Raw arguments are never stored.
- `build_mcp_audit_row(*, server, tool, payload, decision, reason=None, agent_id=None,
  timestamp=None, payload_digest=None) -> dict` — constructs a normalized,
  JSON-serializable audit row. `decision` is a free-form label (e.g. "allow",
  "deny", "observed") that the helper RECORDS but does NOT enforce.
- `MCPAuditLogger` — thin wrapper that owns a `TraceSink` (defaults to
  `JsonlFileSink`) and exposes `.record(...)` writing one row per call. Thread-safe
  via the sink's own lock; the logger holds no mutable state.

Reuse existing primitives: `JsonlFileSink` from `tracing.py`, `_coerce_json_value`
for serialization safety. No new dependencies — `hashlib`, `json`, `datetime` are
all stdlib.

## Files likely to touch

- `sdk/agentguard/mcp_audit.py` (new)
- `sdk/agentguard/__init__.py` (export new names + `__all__`)
- `sdk/tests/test_mcp_audit.py` (new)
- `sdk/tests/test_architecture.py` (add `mcp_audit.py` to `CORE_MODULES`)
- `sdk/examples/mcp_audit_example.py` (new, tiny example)

## What "done" looks like

- [ ] `build_mcp_audit_row` returns a parseable dict with all required fields.
- [ ] `MCPAuditLogger.record(...)` writes exactly one JSONL line per call.
- [ ] Payloads are digested; raw tool arguments never appear in the row.
- [ ] `decision` is recorded as a label; no code path enforces/short-circuits.
- [ ] Unit tests cover allow-style and deny-style row shapes, digest behavior,
      and no-raw-argument-leakage.
- [ ] Existing test suite still passes.
- [ ] No new dependency. No `agentguard47.mcp_policy` module.

## Risks / assumptions

- `test_architecture.py::CORE_MODULES` is an explicit list — a new core module not
  added there is silently uncovered by the stdlib-only check. Mitigation: add it.
- Module must stay stdlib-only (Golden Principle). `hashlib`/`json`/`datetime` only.
- Keep diff under 400 LOC for auto-merge eligibility.
