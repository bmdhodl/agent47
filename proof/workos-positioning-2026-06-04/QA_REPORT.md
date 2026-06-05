# QA Report: WorkOS positioning update

Date: 2026-06-04
Branch: feat/workos-positioning-update
Task: Queue/agent47/workos-positioning-update.md

## Result: PASS

## Checklist
- [x] Docs/markup only (README.md, sdk/PYPI_README.md, site/index.html). No code, tests, workflows, env, or secrets touched.
- [x] No denylist paths (.github/, .env*, supabase/migrations/, security/, secrets, auth config).
- [x] Diff small: 29 insertions, 0 deletions, 3 files (well under 400 LOC).
- [x] No banned words (harness, leverage, streamline, delve, landscape, cutting-edge, game-changer, revolutionary, seamless, robust, holistic, synergy, ecosystem) in added lines.
- [x] No em dashes (U+2014) in added lines.
- [x] No closed-repo mentions (consulting, client work, dashboard internals) introduced. The wedge paragraph is strictly identity-time vs run-time.
- [x] Idempotency: no pre-existing WorkOS mention anywhere in repo before this change.
- [x] sdk/PYPI_README.md regenerated via scripts/generate_pypi_readme.py --write; --check returns exit 0 (in sync).
- [x] PYPI_README is generated, not hand-edited.

## Source verification
Source card: Knowledge/sources/2026-06-04-workos-scoped-agent-credentials.md
- The card is explicit: derived from "TLDR AI Signals" sponsor/marketing copy, confidence = medium, "reading marketing-layer copy, not the SDK or docs."
- No verifiable canonical announcement URL is present in the card.
- Decision: described the capability (per-agent identity, RBAC, audit logs productized by WorkOS in mid-2026) WITHOUT asserting an unverifiable hard link or a precise date. Conservative framing per task instructions.

## Content
The wedge: scoped agent credentials = identity-time (who the agent is, scopes, audit).
AgentGuard = run-time (budget/token/rate cap + in-process kill-switch). They compose,
they do not compete. WorkOS bounds the envelope; AgentGuard enforces it at execution.
