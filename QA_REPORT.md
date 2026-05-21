# QA_REPORT — MCP tool-call audit-log primitive

**Verdict: ✅**

Reviewed the diff (`git diff origin/main...HEAD`) against the queue task,
WORK_PLAN.md, RESEARCH.md, and the repo's AGENTS.md / GOLDEN_PRINCIPLES.md /
architecture tests.

## Scope match

The diff matches WORK_PLAN.md exactly: one new core module, `__init__.py` export
update, one test file, one architecture-test list entry, one example. No scope
creep.

## Acceptance criteria

- [x] Audit helper writes one parseable JSONL row per stub MCP tool call —
      `test_logger_writes_one_jsonl_row_per_call_to_file`.
- [x] Tests cover row schema, digest behavior, and no raw-argument leakage —
      `test_build_row_has_full_schema_*`, `test_digest_*`,
      `test_row_does_not_leak_raw_arguments`, `test_logger_does_not_leak_raw_arguments`.
- [x] Existing suite still passes — 762 passed, 0 failed.
- [x] PR body states audit-only / no policy enforcement.

## Non-goals — all respected

- No `agentguard47.mcp_policy` module.
- No allowlists, denylists, PHI regexes, rate limits, or short-circuit enforcement.
  `decision` is a recorded label; `test_logger_records_decision_label_without_enforcing`
  proves a `"deny"` value still produces a written row with no raise.
- No new dependencies — `mcp_audit.py` is stdlib-only (`hashlib`, `json`,
  `datetime`, `typing`) plus the core `tracing` module. Added to `CORE_MODULES`
  in `test_architecture.py`, and the stdlib-only test passes.
- No public-positioning changes, no blog post.

## Security / safety confirmations

- **No secrets added.** Verified — diff contains no keys, tokens, or credentials.
- **No denylist paths touched.** Diff is confined to `sdk/` plus two root
  artifact docs. No `.github/workflows/`, `.env*`, `supabase/migrations/`,
  `security/`, or auth config.
- **No test coverage regression.** 762 tests pass (291 baseline + new). All
  pre-existing tests still pass; `test_exports.py` and `test_architecture.py`
  were updated to register the three new public names — required, not a
  weakening of the checks.
- **No raw-argument leakage.** `build_mcp_audit_row` never stores `payload`;
  only a `"<algo>:<hexdigest>"` digest. Two tests assert secrets are absent
  from serialized rows.

## Pattern compliance

- Reuses `JsonlFileSink`, `TraceSink`, `_coerce_json_value` rather than
  re-implementing.
- `_require_non_empty` / `_timestamp_now` mirror the existing `decision.py`
  helpers.
- `__init__.py` import grouping and sorted `__all__` follow the existing style.
- Thread safety comes from the sink's own lock; the logger holds no mutable
  state, consistent with the architecture test's `THREAD_SAFE_CLASSES` model.

## Issues

None blocking.

Note for the merge gate: source + test changes total ~499 lines (module 204,
tests 220, wiring 6, example 65); with the two artifact docs the full diff is
588 lines, above the 400-LOC auto-merge threshold. The size is inherent to a
new module plus its test file, not avoidable scope. Flagging per the mechanical
gate.
