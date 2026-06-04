# WORK_PLAN — README positioning vs Anthropic per-tool max_tokens

## Problem statement

On 2026-06-02 Anthropic shipped per-tool `max_tokens` caps on the advisor tool, so first-party Claude API users can now cap output tokens per tool call natively. The current `README.md` positioning still leads with a bare "stop runaway agents before they burn money" pitch and frames `BudgetGuard` primarily as a per-run dollar/call cap. That framing now overlaps with what Anthropic ships out of the box for one-call workloads. AgentGuard's actual moat — cross-provider abstraction, multi-call budget envelopes, rate limits, time windows, and in-process loop/retry/timeout stops — needs to be the headline.

## Approach

Surgical README edit. No code change, no API change. Two narrow inserts plus minimal copy tweaks:

1. Add a short subsection under `## Why AgentGuard` that names the contrast explicitly: "Anthropic per-tool `max_tokens` (single-call output cap)" vs "AgentGuard cross-call / cross-provider budget envelope". One paragraph + one comparison row. This is the headline answer to "why this still exists in June 2026."
2. Add one row to the existing `## Runtime Control vs Observability` table covering per-tool / per-call provider caps, so the comparison is durable next to the other competitive notes.

No other docs touched. PYPI_README, AGENTS.md, ARCHITECTURE.md, landing page (bmdpat) are explicitly out of scope for this PR per queue-worker invocation (bmdpat half held for Patrick).

## Files likely to touch

- `README.md` — the only file changing.

## What "done" looks like

- [ ] README has an explicit "Anthropic per-tool max_tokens" vs "AgentGuard cross-call / cross-provider envelope" comparison.
- [ ] Single-call token cap is described as table-stakes, not the headline.
- [ ] No new dependencies, no API change, no example code changes.
- [ ] Forbidden words from `AGENTS.md` voice rules are not introduced (harness, leverage, streamline, seamless, robust, holistic, synergy, ecosystem, etc.).
- [ ] No em dashes added.
- [ ] Diff under ~60 LOC.

## Risks / assumptions / things that might break

- **Assumption:** Anthropic shipped this on 2026-06-02 per the source card. Verified against the Knowledge source page `2026-06-03-anthropic-advisor-max-tokens-cost-cap.md`. The source card says: per-tool `max_tokens` parameter on the advisor tool definition, output cap per call, plus refusal responses no longer billed when no output generated.
- **Risk:** Over-claim. AgentGuard does not currently claim to wrap every provider's per-tool cap; the contrast must be honest. We position cross-call + cross-provider envelope as the moat, not "we are better at per-call caps than Anthropic."
- **Risk:** Voice drift. Source card uses "narrows the wedge"-style framing; the README must stay builder-to-builder and avoid marketing fluff.
- **Risk:** Markdown table render breakage. Keep new rows inside existing tables; do not introduce a new top-level table format.

## Karpathy-guidelines pass

- Surgical scope: one file, two inserts.
- Verifiable success: explicit text strings ("max_tokens", "per-tool", "cross-call", "cross-provider") will be greppable in the diff.
- Surface assumption: Anthropic's cap is **output-token only, per single call**. If they later ship a multi-call envelope, this positioning has to be revisited.
