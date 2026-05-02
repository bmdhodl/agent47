# Morning Report

## Mission
Implement the top activation recommendation from the product/codebase audit:
make the local SDK proof path more realistic for coding-agent adoption without
changing runtime behavior or adding dependencies.

## What changed
- Added `examples/coding_agent_review_loop.py`, a deterministic offline proof
  that repeated review/edit attempts can burn a run budget and that a stuck
  patch retry storm is stopped by `RetryGuard`.
- Linked the new proof from the README, getting-started guide, and examples
  index so a new user can run it immediately after `agentguard demo`.
- Added a focused test that runs the example in a temporary directory and
  verifies it emits `review.iteration`, `guard.budget_exceeded`, and
  `guard.retry_limit_exceeded` events.
- Regenerated `sdk/PYPI_README.md` so package metadata stays in sync.

## Why it matters
- The repo already has basic offline proof. This adds a more realistic
  coding-agent failure mode: review/refinement loops plus patch retry storms.
- It strengthens the highest-value feature family from the audit: budget and
  runtime enforcement as the first local activation path.
- The change is additive and safe: no public API changes, no dashboard coupling,
  and no new runtime dependencies.

## Validation
- Focused example test passed.
- Direct preflight and release guard passed.
- Ruff, full pytest with coverage, MCP tests, structural tests, Bandit, and
  diff check passed.
- `make` is unavailable in this Windows shell, so Makefile-equivalent commands
  were run directly.

## Follow-up
- Refresh stale roadmap/architecture docs in a separate hygiene PR.
- Consider one opt-in activation metrics design doc, not default SDK telemetry.
- Keep future demos focused on local proof, budget stops, retry stops, and
  incident reports rather than broad observability.
