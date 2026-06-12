# QA_REPORT — competitor wedge map README batch (2026-06-12)

**Verdict: WARN** (one unsupported fact claim in public README copy; everything else passes)

## Checklist

| Check | Result |
|---|---|
| Single wedge-map section covering WorkOS / Uber / per-tool-token-cap axes | PASS — `## How AgentGuard Differs From Adjacent Tools` at README.md:379, one axis table + 4 compose bullets. Routers/gateways row is additive, consistent with WORK_PLAN. |
| mem0 excluded (`grep -i mem0 README.md` empty) | PASS — 0 hits in README.md and sdk/PYPI_README.md. mem0 appears only in internal artifacts (RESEARCH.md/WORK_PLAN.md) documenting the exclusion. |
| Thinking-tokens feature excluded | PASS — no code changes; no README claim of thinking-token accounting. RESEARCH.md "Decisions" deliberately omits even the prose mention (defensible: unshipped capability). |
| Positioning copy only, no feature commits | PASS — diff is README.md, sdk/PYPI_README.md (regenerated), WORK_PLAN.md, RESEARCH.md. One commit, docs only. |
| Voice: no em dashes in added lines | PASS for README/PYPI added lines. Three em dashes in added lines of internal artifacts only (WORK_PLAN.md:1, RESEARCH.md:1, RESEARCH.md:50 quoting repo CLAUDE.md). Not user-facing; noted, not blocking. |
| Voice: banned words in added lines | PASS — only "hit" is WORK_PLAN.md:63 quoting the banned-word grep pattern itself. No banned words in README/PYPI copy. Tone is builder-first, short sentences. |
| Uber fact check vs RESEARCH.md | PASS on the headline claim — README.md:400-402 says "$1,500 per month in token spend on each AI coding tool" (per employee, per tool), matching the source of record. Task card's imprecise "per developer Claude Code cap" was correctly NOT used. |
| **Unsupported claim** | **WARN — README.md:406 "Fortune 50 finance team". Uber is not Fortune 50 (Fortune 500 rank ~#58-#74 in recent lists) and RESEARCH.md cites no rank. Suggest "Fortune 100" or "a $40B company".** |
| sdk/PYPI_README.md regenerated | PASS — `python scripts/generate_pypi_readme.py --check` exit 0. |
| Sync test | PASS — `python -m pytest sdk/tests/test_pypi_readme_sync.py -q` -> 5 passed. |
| Secrets | None added. |
| Denylist paths (.github/workflows/, .env*, supabase/migrations/, security/) | Untouched. |
| Test coverage | No regression — no test files modified or removed. |
| Scope vs WORK_PLAN | Matches — 4 files, 193 insertions / 87 deletions, well under 400 LOC cap. |

## Required fix before merge

1. README.md:406 (and the mirrored line in sdk/PYPI_README.md): replace "Fortune 50" with a supported framing, then regenerate the PyPI README.
