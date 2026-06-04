# QA_REPORT — README containment scope positioning

**Verdict: PASS**

## Checks

### Scope match with WORK_PLAN
- [x] Added a "Scope" block after "Design constraints" list — matches plan.
- [x] One block, 14 LOC added. Under the planned ~30 LOC ceiling.
- [x] Sentence 1 names AgentGuard's scope (runtime budget/token/rate/retry/
      loop/timeout caps, in-process).
- [x] Sentence 2 names OS-level containment as out of scope and lists
      Anthropic's four primitives (process sandboxes, VMs, filesystem
      boundaries, egress controls).
- [x] Anthropic URL present: https://www.anthropic.com/news/how-we-contain-claude

### Done criteria from queue task frontmatter
- [x] `verifier: "agent47 README updated with scope statement that cites
      Anthropic's containment doc as the canonical map for the adjacent gap"`
      — satisfied by the new Scope section.
- [x] `done_artifact: "agent47 README.md PR with positioning paragraph"` —
      this PR.

### Voice / style
- [x] No banned words (harness, leverage, streamline, delve, landscape,
      cutting-edge, game-changer, revolutionary, seamless, robust, holistic,
      synergy, ecosystem) in the new block. Grepped.
- [x] No em-dashes added by this change. Pre-existing em-dashes in
      unrelated section headings are untouched.
- [x] Builder-to-builder tone matches surrounding text (compare to PocketOS
      section: "does not replace least-privilege creds").

### Integration with PR #568
- [x] No duplication with the new cross-call envelope vs. `max_tokens`
      comparison table (lines 76-85). The Scope block is a different
      axis: in-process vs. OS-level. PR #568 contrasts AgentGuard with
      Anthropic's single-call cap; this contrasts AgentGuard with
      Anthropic's process-level containment.
- [x] The "layers are complementary" framing echoes the existing
      "complementary" framing in the "Why AgentGuard" section (line 54),
      which is consistent house style.

### Denylist + safety
- [x] No files in `.github/workflows/`, `.env*`, `supabase/migrations/`,
      `security/`, Stripe/Clerk config, or secrets touched.
- [x] No new dependencies.
- [x] No test coverage regression (docs-only change, no test files
      touched).
- [x] No secrets, credentials, or API keys added.

### Coverage of the queue task requirement
The queue task asks for:
1. "one sentence naming AgentGuard's scope (runtime budget/token/rate caps)"
   — covered in sentence 1.
2. "one sentence noting that OS-level containment (process sandboxes, VMs,
   filesystem boundaries, egress controls) is out of scope, with a link to
   Anthropic's 'How we contain Claude' post"
   — covered in sentence 2 + the markdown link.

### Triple-check stranger-read
Read the new block cold. First sentence names what AgentGuard does.
Second names what it doesn't do and where to look for the adjacent layer.
A closing sentence ties it back to the existing "complementary" framing so
the section doesn't read as defensive disclaimer.

## Issues found

None blocking.
