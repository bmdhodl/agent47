# Skill Progression Hardening Log

Date: 2026-06-12

## Goal

Enhance the five recurring skills surfaced by recent AgentGuard PR review
evidence and keep the work mergeable through the normal PR loop.

## Skills Encoded

1. Fact-ledgered public positioning QA.
2. Cross-platform filesystem and concurrency design.
3. External API collector resilience and data-shape testing.
4. Proof artifact integrity and reproducibility.
5. CI spend, routing, timeout, and review-workflow economics.

## Work Log

- Read `memory/state.md`, `memory/blockers.md`, `memory/decisions.md`,
  `memory/distribution.md`, `ops/00-NORTHSTAR.md`,
  `ops/03-ROADMAP_NOW_NEXT_LATER.md`, and `ops/04-DEFINITION_OF_DONE.md`.
- Noted repo freshness warning: roadmap is older than the 5-day threshold;
  architecture is at the 14-day threshold.
- Created branch `codex/skill-progression-hardening-20260612` from
  `origin/main`.
- Added `.github/PULL_REQUEST_TEMPLATE.md` gates for the five skill areas.
- Hardened `.github/workflows/claude-review.yml` around checkout scope, diff
  truncation, untrusted-diff boundaries, bounded runtime, and Claude CLI pinning.
- Added `scripts/review_readiness_guard.py` plus tests so the five gates and
  review-workflow hardening stay executable.
- Wired the guard into `make check`, `make review-readiness`, and
  `scripts/sdk_preflight.py`.

## Validation

- `python scripts/review_readiness_guard.py` -> passed.
- `python -m pytest sdk/tests/test_review_readiness_guard.py sdk/tests/test_sdk_preflight.py sdk/tests/test_ci_guardrails.py -q` -> 16 passed.
- `python -m ruff check scripts/review_readiness_guard.py scripts/sdk_preflight.py sdk/tests/test_review_readiness_guard.py` -> passed.
- `python scripts/sdk_preflight.py` -> passed changed-file plan and checks.
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py scripts/ci_tools_requirements_guard.py scripts/review_readiness_guard.py` -> passed.
- `python scripts/ci_tools_requirements_guard.py` -> passed.
- `python scripts/generate_pypi_readme.py --check` -> passed.
- `python scripts/sdk_release_guard.py` -> passed.
- `python -m pytest sdk/tests/ -q` -> 812 passed.
- `python -m pytest sdk/tests/test_architecture.py -v` -> 9 passed.
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q` -> passed with no findings.
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80` -> 812 passed, 92.36% coverage.
- `npm --prefix mcp-server ci` with a temporary npm cache, then `npm --prefix mcp-server test` -> 10 passed.
- `python -m pip install -e ./agentguard-mcp`, then local budget MCP ruff + pytest -> 15 passed.

## Open Notes

- `npm view @anthropic-ai/claude-code version` initially failed with ENOSPC in
  the default npm cache; reran with a temporary npm cache and observed `2.1.175`.
- Existing open PRs remain separate; this branch does not merge or close
  unrelated positioning, dependency, or roadmap PRs.
- `npm --prefix mcp-server ci` still reports one moderate transitive `hono`
  advisory. Existing issue #596 and Dependabot PR #570 already track that
  out-of-scope dependency update, so no duplicate GitHub issue was opened.
