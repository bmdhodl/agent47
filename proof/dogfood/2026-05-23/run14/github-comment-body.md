Dogfood operator run14 proof is pushed in `12e15b8`.

Artifacts: `proof/dogfood/2026-05-23/run14/`

Guard proof:
- demo: `guard.budget_warning`, `guard.budget_exceeded` at `$1.0800 > $1.0000`, `guard.loop_detected`, `guard.retry_limit_exceeded`
- review loop: `guard.budget_exceeded` at `$0.0510 > $0.0450`, plus `guard.retry_limit_exceeded` for `apply_patch` attempt 4
- doctor: local setup verification and `agentguard_doctor_trace.jsonl`

Validation:
- focused SDK proof tests: `35 passed in 1.47s`
- release guard: passed
- `git diff --check`: passed
- artifact UTF-8/BOM/NUL/local-path scan: passed
- JSON/JSONL parse scan: passed

Repo health:
- PR #506 was green before this push and remains the consolidated rolling proof PR.
- Open PR thread sweep found 0 active unresolved non-outdated threads before push.
- PR #508 is still failing CI from the setup-go Dependabot bump guardrail expectation.
- Release/package state remains aligned for GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`.

I will recheck CI and review threads after GitHub finishes the refreshed checks for `12e15b8`.