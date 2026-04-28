# WORK_PLAN: OpenAI PII Detection Model Eval (PIIGuard scoping)

## Problem

OpenAI shipped a purpose-built PII detection / masking model (Reddit pointer 2026-04-26). Two questions for AgentGuard: (1) should we ship a `PIIGuard` runtime guard now, with OpenAI as one backend option, or (2) wait until the OpenAI roadmap clarifies whether they will ship a full safety SDK that subsumes this niche? Either answer requires a real eval.

## Approach

Mirror the pattern used for PR #395 (managed-agents-memory scoping): produce a docs/scoping/ markdown that captures pricing, latency, accuracy claims for the OpenAI model, sketches a `PIIGuard` interface (pluggable backend: OpenAI / Presidio / regex), and lands a one-line build/wait/punt recommendation. No feature code in this PR.

This is consistent with the queue task itself, which explicitly permits "or explicit 'wait' decision logged in this task with reason."

## Files likely to touch

- `docs/scoping/openai-pii-guard.md` (new, only meaningful content)
- `WORK_PLAN.md`, `RESEARCH.md`, `QA_REPORT.md` (proof artifacts at repo root, committed per queue-worker workflow)

## Done criteria

- Scoping doc exists with: model facts, pricing, latency, accuracy notes, PIIGuard interface sketch, build/wait/punt recommendation.
- Draft PR open against bmdhodl/agent47.
- Knowledge/entities/openai.md updated with PII model row (separate vault commit, not in this PR).
- Queue task moved to Complete/ with merged=false / verified=skipped.

## Risks / assumptions

- ContentGuard sits in roadmap "Later" bucket. Recommending "wait" aligns with current Now/Next focus (coding-agent positioning + MCP registry readiness).
- OpenAI's official launch material is thin — recommendation should be honest about evidence quality.
- Repo boundary in CLAUDE.md: SDK stays zero-dependency. Any future PIIGuard-OpenAI backend must be an extra (`agentguard47[openai-pii]`), not a hard dep.
