# WORK_PLAN — README containment scope positioning

## Problem

AgentGuard's README does not explicitly name what it is NOT: an OS-level
containment layer. Anthropic published a canonical four-layer containment
taxonomy on 2026-05-30 (process sandboxes, VMs, filesystem boundaries, egress
controls). Without a clear scope statement that cites this reference,
builders evaluating AgentGuard cannot tell where the SDK ends and where
sibling containment primitives begin. PR #568 just added a cross-call
envelope vs. per-tool `max_tokens` comparison; this change adds the adjacent
gap statement.

## Approach

Add a short "Scope" block after the existing "Design constraints" list,
before the "Real Incidents AgentGuard Prevents" section. Two sentences:

1. Name AgentGuard's scope: runtime budget/token/rate caps inside the agent
   process.
2. Name what is out of scope (OS-level containment: process sandboxes, VMs,
   filesystem boundaries, egress controls) and cite Anthropic's "How we
   contain Claude" post as the canonical reference for that layer.

This integrates with PR #568's positioning (in-process exception layer) by
extending the same frame outward: in-process is one layer, OS-level
containment is the adjacent one.

## Files likely to touch

- `README.md` — one block insert (~6 lines) after the Design constraints
  list.

## What "done" looks like

- [ ] README has a "Scope" block naming AgentGuard's runtime budget/token/
      rate scope.
- [ ] The block states OS-level containment is out of scope and lists
      Anthropic's four primitives.
- [ ] A link to https://www.anthropic.com/news/how-we-contain-claude is
      present.
- [ ] No duplication with the existing "Design constraints", "Why
      AgentGuard", or "Threat model: agent data exfiltration" sections.
- [ ] No conflict with PR #568's cross-call envelope framing.
- [ ] No banned voice words. No em dashes. Diff under ~30 LOC.

## Risks / assumptions

- Risk: scope block reads as defensive rather than clarifying. Mitigation:
  same tone as the existing PocketOS section ("does not replace
  least-privilege creds").
- Assumption: Anthropic's URL (`/news/how-we-contain-claude`) is stable. The
  source card at
  `Knowledge/sources/2026-05-30-anthropic-claude-containment-sandbox.md`
  preserves the quotes if the URL moves.
- Risk: voice rules. README uses straight prose, no em-dashes, no fluff
  words. Verified during Triple-check.

## Karpathy-guidelines pass

- Surgical scope: one file, one insert.
- Verifiable success: greppable strings ("process sandboxes", "filesystem
  boundaries", "egress controls", "how-we-contain-claude").
- Surface assumption: Anthropic's four primitives stay the canonical
  taxonomy; if Anthropic publishes a revised taxonomy this paragraph
  revisits.
