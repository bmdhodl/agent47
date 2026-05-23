Dogfood run15 proof is in `proof/dogfood/2026-05-23/run15/`.

Guard behavior observed:
- demo: `guard.budget_warning=1`, `guard.budget_exceeded=1` at `$1.0800 > $1.0000`, `guard.loop_detected=1`, `guard.retry_limit_exceeded=1`
- review loop: `guard.budget_exceeded=1` at `$0.0510 > $0.0450`, `guard.retry_limit_exceeded=1` for `apply_patch` attempt 4

Validation:
- focused dogfood slice: `35 passed in 1.60s`
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed
- review-thread sweep: `0` active unresolved non-outdated threads across open PRs

Repo health:
- PR #506 remains green but blocked on required human review
- PR #508 still has failing Python checks from the setup-go Dependabot bump guardrail expectation
- release/package alignment remains GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`
