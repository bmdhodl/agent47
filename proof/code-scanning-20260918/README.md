# Code scanning / Scorecard pass, 2026-09-18

Scope: GitHub code-scanning alerts uploaded by OpenSSF Scorecard on
`dcebc22` (score 5.9). This is workflow and lockfile hygiene, not an SDK
behavior change.

## Before (Scorecard v5.5.0 on main)

See `scorecard-before.txt`. Actionable alerts in this repo:

- Dangerous-Workflow 0: checkout of `${{ github.event.pull_request.base.sha }}`
  in `.github/workflows/claude-review.yml`
- Pinned-Dependencies 9: unhashed `pip install -e ./agentguard-mcp` in
  `.github/workflows/ci.yml`
- Vulnerabilities 0: 19 PYSECs (aiohttp / chromadb / requests). Reproducing
  `crewai>=0.28` as `*requirements*.txt` is enough for osv-scanner to load
  that extra floor as a live lockfile.

Not in this PR: Fuzzing, CII Best Practices, Code-Review human approvals,
Signed-Releases GitHub assets, optional CrewAI/ChromaDB (`#644`).

## Changes

- Claude review checks out `${{ github.sha }}` (trusted `pull_request_target`
  base commit). The job still never executes the PR tree.
- CI `mcp-budget` installs hashed `.github/requirements/mcp-budget.txt`, then
  runs tests with `PYTHONPATH` instead of an unhashed editable install.
- September audit extra floors were renamed off `*requirements*.txt` so they
  are snapshots, not lockfiles.
- The eval composite action pins `actions/setup-python` by SHA. Claude review
  writes `gh pr diff` to a file and prints CLI stderr.

## Proof

| Artifact | Command | Exit | Platform |
|---|---|---|---|
| `targeted-tests.txt` | `python -m pytest sdk/tests/test_ci_guardrails.py sdk/tests/test_review_readiness_guard.py sdk/tests/test_ci_tools_requirements_guard.py -v` | 0 | linux |
| `review-readiness.txt` | `python scripts/review_readiness_guard.py` | 0 | linux |
| `mcp-budget-install.txt` | hashed `ci-tools.txt` then `mcp-budget.txt`; `PYTHONPATH=. pytest` in `agentguard-mcp` | 0 | linux |
| `osv-notes.txt` | osv-scanner 2.6.0 | 0 | linux |
| `ruff.txt` | `ruff check` on touched Python | 0 | linux |

Regenerated after local review of the targeted suite and full `make check`
(`make-check-summary.txt`: 1049 passed, 1 skipped, 90.48% coverage).
