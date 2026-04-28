# Scoping: OpenAI PII Detection Model + AgentGuard PIIGuard

**Status:** scoping only — no feature code in this PR.
**Date:** 2026-04-27
**Author:** queue-worker (autonomous)
**Source signal:** r/LocalLLaMA thread, 2026-04-26, pointing at a new OpenAI purpose-built PII detection / masking model.

## Why this matters for AgentGuard

AgentGuard's wedge is runtime enforcement: hard stops on budget, loops, retries, timeouts. PII / content enforcement is the natural neighbor — same shape (intercept → evaluate → raise), different signal. The roadmap already lists `ContentGuard` in `ops/03-ROADMAP_NOW_NEXT_LATER.md` "Later" bucket, framed as a regex-based, no-deps guard class.

OpenAI shipping a dedicated model is two things at once:

1. **Opportunity.** A higher-accuracy backend option for a future PIIGuard / ContentGuard, in addition to regex and Presidio.
2. **Competitive signal.** If OpenAI later ships a full safety SDK around this model, the PIIGuard niche shrinks. Doesn't kill AgentGuard (we're cross-provider, runtime, zero-dep), but narrows the addressable land for PII specifically.

Either reaction starts with an eval. This doc captures what we know, what we'd build, and the recommendation.

## What we actually know about the OpenAI model

Honest answer: not enough.

| Question | Answer |
|---|---|
| Model name / endpoint | Not confirmed from this environment |
| Pricing | Not confirmed |
| Latency p50 / p95 | Not benchmarked |
| Accuracy vs Presidio / regex | Not benchmarked |
| Streaming support | Unknown |
| PII categories covered | Unknown (likely: name, email, phone, SSN, address, payment) |
| Deployment shape | Likely API call; possibly available via batch |

Before any feature code: someone benchmarks this on a labeled corpus against Presidio and a baseline regex set. That's a half-day of work that should NOT happen until PIIGuard moves to the "Now" bucket.

## PIIGuard interface sketch

Non-binding. Captures shape so future work doesn't start from zero.

```python
from agentguard import PIIGuard, RegexPIIBackend

guard = PIIGuard(
    backend=RegexPIIBackend(),       # default; zero-dep
    on_detect="raise",               # or "redact" or "warn"
    categories=["email", "phone", "ssn"],
    sample_rate=1.0,                 # check every output
)

# Backends ship as extras to keep core zero-dep:
#   pip install agentguard47[presidio]  -> PresidioPIIBackend
#   pip install agentguard47[openai-pii] -> OpenAIPIIBackend
```

Constraints (from `CLAUDE.md` repo boundary):

- Core SDK stays zero-dependency. `RegexPIIBackend` is the default and ships in core.
- `PresidioPIIBackend` is an optional extra — never a hard dep.
- `OpenAIPIIBackend` is an optional extra — never a hard dep.
- `PIIGuard` raises `ContentViolation` (already named in the Later bucket spec).

Cost dimension: an OpenAI backend introduces an extra API call per guarded output. PIIGuard SHOULD be wrappable in a `BudgetGuard` or its own `PIIBudgetGuard` so users don't accidentally turn safety into a runaway bill. This is the Inception-style guard-the-guard problem and matches how `BudgetAwareEscalation` already works.

## Build / Wait / Punt — recommendation

**Wait.** Re-evaluate when one of these signals fires:

1. A real customer asks for PII enforcement at runtime (not a hypothetical).
2. ContentGuard / PIIGuard moves to the "Now" or "Next" bucket in `ops/03-ROADMAP_NOW_NEXT_LATER.md`.
3. OpenAI publishes official model + pricing docs AND someone wants to benchmark.

Reasons to wait, not punt:

- PIIGuard fits North Star (runtime enforcement, not framework, not observability).
- OpenAI's model materially raises the ceiling on accuracy for a future backend, so the option is more valuable now than it was 6 months ago.
- The right time is after current "Now" items (coding-agent positioning, MCP registry readiness, install-to-first-guard) are done — those have direct adoption payoff. PIIGuard is a feature add, not a wedge sharpener.

Reasons NOT to ship now:

- Now bucket has 4 active items. Adding a 5th violates the focus rule.
- No real customer ask in hand at compile time.
- Building against an unbenchmarked model = vibe-coded backend. Worse than having no backend.
- The hardest part of PIIGuard isn't the OpenAI integration; it's the interface, redaction policy, and on_detect contract. None of that is unblocked by OpenAI's model.

## What this PR is NOT

- Not a feature commitment.
- Not a deprecation of the regex / Presidio path.
- Not a benchmark.
- Not a public roadmap change.

Updating `ops/03-ROADMAP_NOW_NEXT_LATER.md` to promote ContentGuard out of "Later" is a separate decision, made by Patrick, not by this scoping doc.

## Resume path

If/when this gets greenlit:

1. Promote ContentGuard / PIIGuard from "Later" to "Next" or "Now" in `ops/03-ROADMAP_NOW_NEXT_LATER.md`.
2. Verify OpenAI model name, pricing, latency from official docs.
3. Build a labeled-corpus benchmark covering the 6 standard PII categories. Score: regex baseline vs Presidio vs OpenAI.
4. Implement `PIIGuard` with `RegexPIIBackend` first (in core, zero-dep).
5. Add `agentguard47[presidio]` extra second.
6. Add `agentguard47[openai-pii]` extra third, only if benchmark justifies it.
7. Document `on_detect` contract: raise, redact, warn, sample_rate, categories.
8. Test coverage parity with `BudgetGuard` (≥90% line coverage on the guard class).
