# Morning Report

## Mission
Make the SDK feel like the clean local entry point into the AgentGuard runtime
control plane, while staying aligned with the hosted dashboard contract.

## What changed
- Decision helpers now default `binding_state` to dashboard-parseable states:
  `proposed`, `edited`, `overridden`, and `approved`.
- The local ingest test harness now mirrors dashboard decision-trace warnings,
  including the case where an event is accepted but not queryable as decision
  history.
- README, SDK README, quickstart guides, examples, and package metadata now lead
  with the local runtime-control proof path and explain what hosted dashboard
  ingest adds.
- Added `docs/guides/dashboard-contract.md` to document ingest shape, decision
  event names, required fields, and the remote-kill polling boundary.

## Why it matters
- The dashboard requires `binding_state` to be a non-empty string for decision
  history extraction. The SDK previously emitted `None` by default for several
  decision event types, which could make traces ingest successfully but fail
  downstream decision indexing.
- The docs now match the product story: start local with zero dependencies, add
  hosted dashboard when history, alerts, team visibility, or remote kill signal
  management matter.
- The SDK no longer implies that `HttpSink` alone executes remote kill signals.

## Validation
- Focused decision and ingest contract tests pass.
- Full SDK test suite passes: `693 passed`, coverage `92.88%`.
- Ruff, MCP tests, structural checks, bandit, release guard, and preflight pass.
- `make` is unavailable in this Windows shell, so Makefile-equivalent commands
  were run directly.

## Follow-up
- If remote kill should become a first-class SDK feature, design an explicit
  zero-dependency polling helper with short timeouts, bounded polling, and
  opt-in failure policy.
- Keep the dashboard decision schema and SDK `decision.py` helper defaults in
  lockstep on future changes.
