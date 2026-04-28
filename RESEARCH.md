# RESEARCH: OpenAI PII Detection Model

## Source signal

- Origin: `Knowledge/sources/2026-04-26-openai-pii-detection-model.md` (vault).
- Public pointer: r/LocalLLaMA thread referencing a new OpenAI PII detection / masking model. Marketing copy and exact pricing not yet on platform.openai.com docs at compile time.

## What we know vs. what's hand-waving

| Claim | Source quality | Notes |
|---|---|---|
| OpenAI shipped a PII model | Reddit thread + OP screenshot | Plausible, not verified against official changelog from this environment |
| Designed for detection + masking | Reddit OP description | Consistent with what a "purpose-built" model in this niche would do |
| Pricing | Not stated | Must wait for official docs |
| Latency | Not stated | Must wait for official docs or local benchmark |
| Accuracy vs Presidio / regex | Not benchmarked | Eval-only path requires building or finding a labeled corpus |

## Existing AgentGuard repo evidence

- `ops/03-ROADMAP_NOW_NEXT_LATER.md` lists `ContentGuard - detect PII/sensitive data in agent outputs` in the **Later** bucket. Already framed as a regex-based, no-deps guard class raising `ContentViolation`.
- `ops/00-NORTHSTAR.md` non-goals exclude "framework" and "full observability" but do NOT exclude content/PII enforcement at runtime — runtime enforcement is exactly the wedge.
- `CLAUDE.md` repo boundary: "SDK stays free, MIT, and zero-dependency". Any OpenAI backend MUST be an optional extra.
- Now bucket is "coding-agent positioning + MCP registry readiness + install-to-first-guard proof hardening". PII work is a distraction from the current 2-week focus.

## Patterns to copy

- PR #395 (`docs/scoping/managed-agents-memory.md`) — same shape: scoping doc, draft PR, no feature code, build/wait/punt recommendation. Worked. Repeat.

## Decision logic

1. PIIGuard belongs in the AgentGuard vision (it's runtime safety, not framework or observability).
2. It's already explicitly "Later" in roadmap.
3. OpenAI shipping a backend option does NOT change priority — it just means **when** we build PIIGuard, OpenAI is one of N backends.
4. Now bucket has 4 active items already. 1-2 Builders rule + Now-bucket discipline = no.
5. Recommendation: **wait**. Re-evaluate when one of the Now items completes OR when a real customer asks for PII enforcement.
