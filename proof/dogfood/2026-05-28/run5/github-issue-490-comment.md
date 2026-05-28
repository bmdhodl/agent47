## 2026-05-28 run5 dogfood proof

Artifacts:
- PR: https://github.com/bmdhodl/agent47/pull/537
- Commit: `ffa92bb`
- Proof bundle: `proof/dogfood/2026-05-28/run5/`
- Summary: `proof/dogfood/2026-05-28/run5/summary.md`
- Trace inspection: `proof/dogfood/2026-05-28/run5/trace_inspection.txt`
- Parsed guard events: `proof/dogfood/2026-05-28/run5/guard_events.json`

Commands/proof:
- PATH `agentguard doctor` and `agentguard demo` ran with trace files in the proof bundle.
- PowerShell set `$env:PYTHONPATH='./sdk'` before the checkout-bound `python -m agentguard.cli doctor`, `demo`, `report`, `incident`, and review-loop example commands.
- `python examples/coding_agent_review_loop.py` produced the review-loop trace.
- `agentguard report` counted 36 total demo events and 4 guard events.
- `agentguard incident` classified the review-loop trace as `Status: incident`, `Severity: critical`, `Primary cause: retry_limit_exceeded`.

Concrete guard behavior:
- Demo emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Review loop stopped at `$0.0510 > $0.0450`.
- RetryGuard stopped `apply_patch` on attempt 4 with a limit of 3.

Validation:
- Focused pytest slice: 35 passed.
- Release guard with npm check: passed.
- `git diff --check`: passed.
- Artifact validation: required files present, JSON parses, no UTF-8 BOM, no local worktree path leak.

Repo health notes:
- Latest release/PyPI/local SDK are aligned at `1.2.10`; npm/local MCP are aligned at `0.2.2`.
- Ops docs are stale by cadence (`ops/03` 3 weeks, `ops/02` 4 weeks) and remain tracked in #473.
- PR #508 still has failed/cancelled test jobs; green dogfood proof PRs remain review-blocked.
