# RESEARCH — verification of WORK_PLAN assumptions

## Existing decision/audit surface

- `sdk/agentguard/decision.py` — decision events (`decision.proposed/edited/...`)
  are emitted as **trace events** through a `TraceContext`. They are span-bound and
  carry proposal/final/diff. This is review-flow oriented, not per-tool-call audit.
  Reusing `DecisionTrace` would force MCP calls into a span/workflow model they do
  not have. Decision: build a standalone row-writer that reuses only the sink.
- `sdk/agentguard/tracing.py:67` — `JsonlFileSink(path)`: thread-safe, appends one
  `json.dumps(event, sort_keys=True)` line per `emit()`. Exactly the sink semantics
  needed. `StdoutSink` and the `TraceSink` ABC are also reusable.
- `sdk/agentguard/tracing.py:97` — `_coerce_json_value()` recursively coerces
  arbitrary values into JSON-serializable structures (bytes, sets, non-serializable
  fall back to a marker). Used to make the digest input deterministic and safe.

## Architecture constraints (GOLDEN_PRINCIPLES.md / test_architecture.py)

- `tests/test_architecture.py:27` `CORE_MODULES` is an explicit list; the
  stdlib-only import test (line 175) and the public-API test (line 218) iterate it.
  A new core module MUST be added to that list or it is not covered. Verified by
  reading lines 175-260.
- `MAX_MODULE_LINES = 800`, enforced via `rglob` (line 253) — new module is well
  under.
- `test_no_hardcoded_absolute_paths` (line 308) rglobs all files — example/module
  must use relative paths only.
- Core modules must be stdlib-only. `hashlib`, `json`, `datetime`, `threading` are
  all stdlib — no new dependency, satisfies the explicit non-goal.

## Package export pattern

- `sdk/agentguard/__init__.py` imports public names per-module and lists every one
  in a sorted `__all__`. New names (`MCPAuditLogger`, `build_mcp_audit_row`,
  `digest_payload`) follow that pattern.

## Conclusion

Plan holds. Build a standalone stdlib-only `mcp_audit.py` that reuses `JsonlFileSink`
and `_coerce_json_value`; do not route through `DecisionTrace`. Add the module to
`CORE_MODULES`. No policy enforcement anywhere — `decision` is a recorded string.
