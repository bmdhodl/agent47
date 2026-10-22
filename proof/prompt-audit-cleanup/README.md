# Prompt-audit cleanup proof (2026-10-04)

A prompt audit of the Claude Code configuration (target model: Claude Opus 5.5)
found stale facts, broken references, and conflicts between instruction files.
This change fixes them. Docs and agent config only; no SDK code changed.

## Changes, by finding

| ID | File | Change | Repo evidence |
|---|---|---|---|
| P01 | `AGENTS.md` | `.Codex/agents/` → `.claude/agents/` | `.Codex/agents/` does not exist |
| P02 | `AGENTS.md` | dropped `(Codex.ai/code)` | rename leftover from `23b800f` |
| P03 | `AGENTS.md` | staleness check reads root `ARCHITECTURE.md` | `CLAUDE.md:47-48`, `ARCHITECTURE.md:116` |
| P04 | `AGENTS.md` | `PYPI_TOKEN` → Trusted Publishing (OIDC) | `.github/workflows/publish.yml` |
| P05 | `AGENTS.md` | old module graph/table → pointer to `ARCHITECTURE.md` | `cost.py` and `guards.py` imports; 13 CLI subcommands |
| P06 | `.agents/skills/next-ticket/SKILL.md` | dropped the AG-06 hold | #735 and #767 closed |
| P07 | `.claude/agents/pm.md` | `v1.2.6` → `memory/state.md` | `memory/state.md` |
| P08 | `.claude/agents/pm.md` | 3-phase plan → #729 order | `pm.md:49`, `SKILL.md:20` |
| P09 | `.claude/agents/sdk-dev.md` | link `../../GOLDEN_PRINCIPLES.md` | file is at the repo root |
| P10 | `.claude/agents/sdk-dev.md` | `RateLimitExceeded` → `RetryLimitExceeded` | no `RateLimitExceeded` in the SDK |
| P11 | `.claude/agents/sdk-dev.md` | `MODEL_PRICES` → `DEFAULT_PRICE_TABLE` | `price_table.py`, `cost.py:23` |
| P12 | `.claude/agents/marketing.md` | Phase 1 table → #729 | `SKILL.md:20` |
| P13 | `.claude/agents/marketing.md` | no move to broad observability | `CLAUDE.md:74` |
| P14 | `.claude/agents/dashboard-dev.md` | removed non-public prices | `marketing.md:51`, `site/compare.html:146` |
| P15 | `sdk-dev.md`, `pm.md` | added `name`/`description` frontmatter | `CLAUDE.md` lists both as Claude assets |
| P16-P18 | `marketing.md`, `sdk-dev.md` | wedge, audience, product line match current docs | `memory/distribution.md`, `docs/enforcement-boundary.md` |
| P19 | `AGENTS.md` | dropped undated 93% coverage figure | `ci.yml` enforces 80% |
| P20-P22 | `AGENTS.md`, `CLAUDE.md` | removed shouted capitals; rules unchanged | wording only |

Follow-ups for the root report files and the `ops/02` cadence tracking are in
`ops/FOLLOWUP.md`.

## Checks

`make` is not installed on this Windows host, so each target ran directly.
Output files are next to this README.

| File | Command | Result |
|---|---|---|
| `01-preflight.txt` | `python scripts/sdk_preflight.py` | exit 0 (no SDK-relevant changes) |
| `02-ci-tools-guard.txt` | `python scripts/ci_tools_requirements_guard.py` | exit 0 |
| `03-review-readiness.txt` | `python scripts/review_readiness_guard.py` | exit 0 |
| `04-lint.txt` | `ruff check` (Makefile `lint` paths) | exit 0 |
| `05-structural.txt` | `pytest sdk/tests/test_architecture.py` | 9 passed |
| `06-security.txt` | `bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q` | exit 0 |
| `07-release-guard.txt` | `python scripts/sdk_release_guard.py` | Release guard passed |
| `08-pypi-readme-check.txt` | `python scripts/generate_pypi_readme.py --check` | exit 0 |
| `09-test.txt` | `pytest sdk/tests/ --cov=agentguard --cov-fail-under=80` | 1591 passed, 3 skipped; coverage 92.50% |

Not run: `make mcp` (`npm --prefix mcp-server test`). No `mcp-server/` file
changed, and this worktree has no `node_modules`. CI runs it.

`09-test.txt` ends with a `PermissionError` from pytest's `atexit` temp-dir
cleanup. It comes after the summary line. Python ignores it, and pytest
exited 0.

The release-guard markers in `AGENTS.md`, `CLAUDE.md` and `sdk-dev.md` are
unchanged.

## Re-check

`python proof/prompt-audit-cleanup/verify.py` checks each fix against the
repo fact behind it, checks that the saved outputs exited 0, and runs the
release guard. It prints `Verified prompt-audit cleanup`. It fails if, for
example, `pm.md` names `v1.2.6` again.
