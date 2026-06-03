# WORK_PLAN.md - anthropic-advisor-max-tokens-update-positioning (agent47)

## Problem statement

On 2026-06-02 Anthropic shipped per-tool `max_tokens` caps on the advisor tool. That narrows the bare "you need a third-party library to cap tokens" pitch for callers already on the first-party Claude API. AgentGuard's actual moat is cross-call and cross-provider budget enforcement, runtime loop/retry/rate guards, and language-agnostic enforcement that survives provider migrations. The README needs to make that explicit so a reader who heard about the Anthropic change does not conclude AgentGuard is now redundant.

## Approach

Surgical README edit:
1. Lightly reframe the "Why AgentGuard" lead paragraph to say in one line that the guard sits across calls, retries, and providers, not just inside a single call.
2. Add a new section "Anthropic per-tool max_tokens vs AgentGuard cross-call/cross-provider budget" just after the existing "Runtime Control vs Observability" section. Short comparison table + one paragraph that says: single-call output cap (Anthropic) and multi-call/multi-provider envelope (AgentGuard) are complementary, not substitutes.
3. Run `scripts/generate_pypi_readme.py` so `sdk/PYPI_README.md` stays in sync (enforced by `test_committed_pypi_readme_is_in_sync`).

No core feature changes. No new dependencies. No code under `sdk/`. No `.github/workflows/` edits. Comparison framing is factual and only describes what each tool does today.

## Files likely to touch

- `README.md` (the lead-paragraph reframe + new comparison section)
- `sdk/PYPI_README.md` (regenerated, not hand-edited)

## What "done" looks like

- [ ] `README.md` lead-paragraph reframed to mention cross-call / cross-provider envelope.
- [ ] `README.md` has a new section comparing Anthropic per-tool `max_tokens` and AgentGuard's multi-call/multi-provider budget.
- [ ] `sdk/PYPI_README.md` regenerated and matches generator output.
- [ ] `pytest sdk/tests/test_pypi_readme_sync.py` passes.
- [ ] PR opened against `bmdhodl/agent47`.

## Risks / assumptions

- Risk: `test_pypi_readme_sync.py` fails if I forget to regenerate. Mitigation: run the regenerate script as the last step before commit.
- Risk: Banned words leak in (harness, leverage, etc.). Mitigation: grep the diff before commit.
- Risk: New section grows past 400 LOC budget. Mitigation: keep section ~30 lines.
- Assumption: the linked Knowledge source page (2026-06-03-anthropic-advisor-max-tokens-cost-cap) accurately summarizes the Anthropic announcement. Verified by reading the source page.
