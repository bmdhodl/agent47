# Scoping: Anthropic Managed Agents Memory cost telemetry

**Status:** Scoping (no implementation yet)
**Last reviewed:** 2026-04-27
**Trigger:** Memory for Claude Managed Agents went public beta on 2026-04-23 under the `managed-agents-2026-04-01` API header.

## Problem

AgentGuard's pitch is "zero-dependency runtime guard for any agent." The hard
budget cap, loop guard, and retry guard all model the cost surfaces that exist
today: prompt tokens, completion tokens, tool calls, retries, wall time.

Anthropic's new managed-agents memory adds a cost surface AgentGuard does not
model: persistent state read/written across runs, with retrieval tokens billed
on read and storage retention billed over time. If a customer adopts memory and
their bill spikes, AgentGuard's "we guard your entire agent budget" claim has a
visible gap.

This doc scopes whether to close that gap, when, and how — without committing
to ship anything yet.

## What memory adds to the cost surface

Based on Anthropic's "Using agent memory" guide (managed-agents header,
2026-04-23), four distinct cost dimensions show up that today's `BudgetGuard`
does not see:

1. **Memory write tokens.** Tokens stored to long-term memory at the end of a
   turn or run. Billed once at write time.
2. **Memory read / retrieval tokens.** Tokens loaded back into the agent's
   context on subsequent turns. Billed every retrieval, can compound if memory
   grows unbounded.
3. **Memory retention.** Storage cost over time for whatever the agent has
   written. Smaller per-token, but accrues without an obvious "agent run" event
   to trigger AgentGuard's per-run hooks.
4. **Implicit context inflation.** Memory retrieval inflates the prompt token
   count of every subsequent turn. This one IS already captured by
   `BudgetGuard` indirectly (because prompt tokens are counted), but the user
   can't see how much of the spend came from memory versus the original prompt.

Of these, (1) and (2) are per-event and map cleanly to existing AgentGuard
counters. (3) is the awkward one: storage retention is not a runtime event, so
the SDK has nothing to instrument unless the host process polls.

## How AgentGuard would surface them

Working sketch — not a commitment:

### New counters
- `memory.write_tokens` — incremented on each write event
- `memory.read_tokens` — incremented on each retrieval event
- `memory.retained_tokens` (gauge, not counter) — current size of stored memory
- `memory.events` — total read/write events this run

### New budget rules
- `max_memory_write_tokens_per_run` — per-run cap on what an agent can stash
- `max_memory_read_tokens_per_run` — per-run cap on retrieval cost
- `max_total_memory_tokens` — gauge cap on storage size; raises if exceeded at
  write time

### Default limits
Conservative defaults consistent with the rest of AgentGuard's "fail loud"
stance: zero memory writes/reads allowed unless the user opts in via
`MemoryGuard(enabled=True, ...)`. The SDK is supposed to surprise no one with
hidden token spend; memory is a brand-new spend surface, so opt-in is the right
default.

### Surface area
A new `MemoryGuard` class living next to `BudgetGuard` in `sdk/agentguard/`,
following the same pattern (constructor takes limits, `check()` raises a
typed exception when tripped, `Tracer` emits `memory.*` events).

## Build / wait / punt

Three honest options.

### Build now (this quarter)
- Pros: AgentGuard ships memory telemetry while memory is still in beta and
  most customers haven't hit the bill yet. Strongest "we cover everything"
  story. Distinguishes from competitors who are still catching up to memory.
- Cons: API is beta — Anthropic explicitly reserves the right to change the
  shape. Building against a moving target risks rework. Memory is also
  Anthropic-specific; OpenAI/Google have different memory models. Hard to
  generalize.

### Wait for GA (recommendation)
- Pros: Anthropic stabilizes the cost-event shape before we instrument it. We
  get to see what real customers do with memory before guessing default limits.
  Memory adoption is currently low; the bill-surprise risk is small in the next
  4-8 weeks. We can land coding-agent positioning (current "Now" roadmap item)
  without a detour.
- Cons: Competitive positioning gap if a competitor ships memory cost telemetry
  first. Mitigation: this scoping doc, plus a one-line "memory telemetry
  arriving with GA" note in the SDK README, neutralizes the optics.

### Punt
- Pros: Memory may stay niche. AgentGuard's `BudgetGuard` already catches the
  blast radius (total spend exceeds cap, agent dies), even if the line-item
  attribution is missing. Customers who don't care about attribution don't care
  about this gap.
- Cons: "We guard your entire agent budget" is the claim on the marketing
  page. Punting permanently means revising the claim. Not worth it.

## Recommendation

**Wait for GA.** Track the beta. Re-scope when Anthropic announces GA or when
a paying customer asks. Keep this doc as the wedge for the eventual
`MemoryGuard` PR — the surface and defaults sketched above are the starting
point.

Specifically:
- Do not start `MemoryGuard` implementation this sprint.
- Do not add a `agentguard47[anthropic-memory]` extra yet — extras are cheap to
  add later and committing to the name now bakes in an assumption that we'll
  ship it as an extra rather than core. That's a Build-time decision, not a
  Wait-time decision.
- Add memory to the watchlist (Anthropic release notes; competitor SDK
  changelogs) so we hear about GA the day it ships.

## Open questions for re-scope at GA time

- Does Anthropic expose memory cost as a separate billing line, or rolled into
  prompt/completion tokens? This determines whether we need a new counter or
  can derive memory cost from existing token fields.
- Do other providers (OpenAI working sets, Google Gemini Enterprise memory)
  converge on a similar shape? If yes, generalize to `MemoryGuard`. If no,
  ship Anthropic-specific first under an extra.
- What is the right default `max_total_memory_tokens` cap? Need a few real
  customer integrations to calibrate; today it would be a guess.

## References
- Anthropic release notes 2026-04-23: <https://platform.claude.com/docs/en/release-notes/overview#april-23-2026>
- Anthropic "Using agent memory" guide (managed-agents-2026-04-01 header)
- Source card: `Knowledge/sources/2026-04-23-claude-managed-agents-memory-beta.md` (vault)
