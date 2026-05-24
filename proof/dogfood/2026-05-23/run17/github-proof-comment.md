Dogfood operator run17 proof is in `proof/dogfood/2026-05-23/run17/`.

Concrete guard behavior observed:
- demo: `guard.budget_warning`, `guard.budget_exceeded` at `$1.0800 > $1.0000`, `guard.loop_detected`, and `guard.retry_limit_exceeded`
- review loop: `guard.budget_exceeded` at `$0.0510 > $0.0450` on attempt 3, plus `guard.retry_limit_exceeded` for `apply_patch` attempt 4
- doctor: local setup verification emitted `doctor.verify` events

Validation:
- focused proof tests: `35 passed in 1.47s`
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed
- `git diff --check`: passed
- artifact hygiene: no local path leaks, BOMs, NUL bytes, or JSON parse failures

Repo health:
- PR #506 remains the consolidated rolling proof PR and is blocked only on required human review.
- Open PR review-thread sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.
- PR #508 still has failing CI from the setup-go Dependabot bump guardrail expectation.
- Release/package state remains aligned for GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`.
- Distribution drift remains: MCP Registry reports `0.2.1`; Glama returns `tools: []`.
