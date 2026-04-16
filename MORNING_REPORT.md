# Morning Report

## Mission
Ship a portable advisor-style escalation guard in the public SDK without breaking the zero-dependency, local-first boundary.

## What shipped
- added `BudgetAwareEscalation`, `EscalationSignal`, and `EscalationRequired`
- supported four v1 escalation triggers: token count, confidence, tool-call depth, and a custom rule
- split the feature into a new stdlib-only `sdk/agentguard/escalation.py` core module so `guards.py` stayed under the repo's line-limit rule
- added a local Llama-to-Claude worked example plus a guide page
- updated README, examples docs, roadmap, changelog, and generated PyPI README

## Why it matters
- the SDK had hard stop guards, but no portable way to keep a cheap model on by default and escalate only the hard turns
- this gives users an advisor-style pattern without locking the repo to Anthropic's server-side tool or any hosted control plane
- the feature stays local-first: the guard decides, the app routes

## Validation
- full SDK suite passed: `687 passed`
- coverage passed at `92.75%`
- lint, structural checks, release guard, preflight, and bandit passed
- local example run produced both console proof and a trace artifact under `proof/budget-aware-escalation/`

## Notes
- I did not repeat the queue note's exact "more than doubled benchmark score" line in repo docs because I could not verify that exact wording from the primary Anthropic doc available in this environment
- the feature is intentionally explicit rather than "magic routing" inside provider patchers
