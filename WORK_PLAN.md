# WORK_PLAN — competitor wedge map README batch (2026-06-12)

## Problem statement

Competitor-positioning signals (WorkOS scoped agent credentials, Uber's per-tool
spend caps, Anthropic per-tool `max_tokens`) currently spawn one paragraph + one
PR each. Per the 2026-06-07 batching rule, they accumulate into ONE
"wedge map" README section refreshed in batch. The README has scattered
positioning (Manifest/gateway in "Why AgentGuard", a per-tool `max_tokens`
table, "Runtime Control vs Observability") but no unified adjacent-tools wedge
map, no WorkOS positioning, and no Uber cap reference.

## Approach

Add one new section, `## How AgentGuard Differs From Adjacent Tools`,
immediately after "Runtime Control vs Observability" in README.md. One axis
table (WorkOS, org per-tool spend caps / Uber pattern, provider per-call token
caps, routers/gateways) plus four short compose bullets. Then regenerate
`sdk/PYPI_README.md` (generated from README.md; CI test
`test_committed_pypi_readme_is_in_sync` fails otherwise).

Explicit exclusions per the task card and fact-gating rule:
- NO mem0 / memory-layer contamination claim (57-71% stat disputed, held on
  Requests/2026-06-04-2330-blocked-decision-mem0-blog-false-stat.md).
- NO thinking-tokens parsing feature (cannon-paused). Also no prose claim of
  thinking-token accounting: the card says "may mention", but the parsing
  feature is unshipped, so claiming it in the README would be a false
  capability claim. Omitted deliberately.
- No feature commits. Copy only.

Fact correction applied: the task card says "Uber's $1,500/developer Claude
Code cap". The source of record (Bloomberg via Simon Willison, 2026-06-03)
says $1,500/month per employee per AI coding tool. README copy uses the
accurate form.

## Files likely to touch

- README.md (new section, ~35 lines)
- sdk/PYPI_README.md (regenerated)
- WORK_PLAN.md / RESEARCH.md / QA_REPORT.md (existing root artifacts, refreshed)

## What "done" looks like

- [ ] README has one "How AgentGuard Differs From Adjacent Tools" section
      covering WorkOS (identity-time vs run-time), Uber org-cap pattern
      (policy-time vs call-site), per-tool token caps (per-call vs run
      envelope), routers/gateways (network vs in-process).
- [ ] No mem0 mention anywhere in README.
- [ ] sdk/PYPI_README.md regenerated and in sync.
- [ ] Voice rules hold: no em dashes, no banned words.
- [ ] Single PR, <= 400 LOC changed, no new deps, no denylist paths.

## Verification commands

Run from repo root. All of 1-3 FAILED (no match) before implementation
(verified 2026-06-12).

1. `grep -c "How AgentGuard Differs From Adjacent Tools" README.md` -> >= 1 after
2. `grep -c "WorkOS" README.md` -> >= 1 after
3. `grep -c "1,500" README.md` -> >= 1 after
4. NEGATIVE: `grep -ci "mem0" README.md` -> 0 before AND after
5. `python scripts/generate_pypi_readme.py --check` -> exit 0 after regen
6. NEGATIVE (banned words): `grep -Ei "leverage|streamline|delve|cutting-edge|game-changer|revolutionary|seamless|robust|holistic|synergy|ecosystem" README.md` -> no new hits vs baseline
7. `python -m pytest sdk/tests/test_pypi_readme_sync.py -q` -> pass

## Risks / assumptions

- Risk: duplication with existing "Why AgentGuard" Manifest/max_tokens copy.
  Mitigation: wedge map is the consolidated cross-tool view; it states each
  axis in one line and links the existing competitive notes. Kept short.
- Assumption: WorkOS positioning is composable ("they stack"), per the
  2026-06-04 source (identity-time vs run-time, same buyer, different wedge).
- PR consolidation of #574/#575/#567/#578/#579 is flagged for Patrick in the
  task card; this worker does not close or reference PR #574.
