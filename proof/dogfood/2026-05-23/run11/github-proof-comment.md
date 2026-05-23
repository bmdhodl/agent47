Dogfood operator run11 proof is pushed in `3a61407`.

Artifacts: `proof/dogfood/2026-05-23/run11/`

Guard proof:
- demo: `guard.budget_warning`, `guard.budget_exceeded` at `$1.0800 > $1.0000`, `guard.loop_detected`, `guard.retry_limit_exceeded`
- review loop: `guard.budget_exceeded` at `$0.0510 > $0.0450`, plus `guard.retry_limit_exceeded` for `apply_patch` attempt 4
- doctor trace: `doctor.verify` start/end events

Validation:
- focused SDK proof tests: `35 passed in 1.54s`
- release guard: passed
- `git diff --check`: passed
- artifact UTF-8/BOM/NUL/local-path/JSON scan: passed

Repo health:
- PR #506 had 0 active unresolved non-outdated review threads before push and remains `REVIEW_REQUIRED`.
- Full open-PR thread sweep found 0 active unresolved non-outdated threads across 25 open PRs before push.
- PR #508 is still failing CI from the setup-go Dependabot bump guardrail expectation.
- Release/package state remains aligned for GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`; MCP Registry timed out from this host, and Glama still reports `tools=[]`.

I will recheck CI and review threads after GitHub finishes the refreshed checks for `3a61407`.
