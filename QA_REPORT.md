# QA_REPORT — README positioning vs Anthropic per-tool max_tokens

Verdict: ✅

## Scope alignment

- Task: reframe README positioning to lead with cross-call / cross-provider envelope, contrast against Anthropic per-tool `max_tokens`.
- Diff: one file (`README.md`), +32 / -2 lines.
- All claims in `WORK_PLAN.md` checked against the actual diff:
  - "Add subsection under Why AgentGuard with explicit contrast" → done at `README.md:56-64`.
  - "Add comparison row to Runtime Control vs Observability table" → done at `README.md:323` (`Cross-call, cross-provider budget envelope | Yes`) plus a follow-up paragraph at `README.md:332-335`.
  - "No code change, no API change" → confirmed, only README touched.
  - "Diff under ~60 LOC" → 32 README insertions, well under.

## Pattern check

- Markdown tables follow the same `| col | col |` style as the rest of the README.
- Wikilinks / footnotes match existing format.
- Bolding uses `**...**` consistent with the doc.

## Voice / brand check (per vault `AGENTS.md`)

- Forbidden words grep: zero matches in `README.md` for `harness|leverage|streamline|delve|landscape|cutting-edge|game-changer|revolutionary|seamless|robust|holistic|synergy|ecosystem|engagement|retainer`.
- Em-dash check: I removed one em-dash on line 53 (replaced with comma) and added zero new em-dashes. Net em-dash count in the file went down by one. (Pre-existing em-dashes in code-block comments and other sections are unchanged.)
- First-person / builder voice preserved. No marketing fluff added.

## Denylist / safety

- No files touched in `.github/workflows/`, `.env*`, `supabase/migrations/`, `security/`, Stripe/Clerk config, or secrets.
- No new dependencies.
- No tests removed or skipped (no test files touched).
- No new external network calls in code (the new release-notes URL is in markdown only).

## Honest scope of claim

- The contrast against Anthropic is bounded to what they actually shipped: per-tool `max_tokens` on the advisor tool, output tokens only, single call. The README does not over-claim that AgentGuard is "better at single-call caps" — it explicitly says single-call caps are table stakes and the moat is the cross-call envelope.
- The release-notes URL is taken from the queue task frontmatter, which references the same source card.

## Independent verifier

Not security-flagged in the task frontmatter (`signal_type: vendor-announcement`, not `security-threat`). Standard self-QA applies; CVE-Bench independent verifier requirement does not.

## Files inspected

- `README.md` — modified, re-read in place after edit.
- `WORK_PLAN.md`, `RESEARCH.md` — refreshed for this task.
- `Knowledge/sources/2026-06-03-anthropic-advisor-max-tokens-cost-cap.md` (vault) — source of truth for the Anthropic change.
- `Queue/agent47/anthropic-advisor-max-tokens-update-positioning.md` (vault) — task spec.

## Confirmation

No secrets added. No denylist paths touched. No test coverage regressions (no tests changed).
