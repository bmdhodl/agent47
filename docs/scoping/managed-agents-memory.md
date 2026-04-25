# Scoping: Anthropic Managed Agents Memory in AgentGuard

**Status:** scoping (no code yet)
**Date:** 2026-04-25
**Author:** AgentGuard maintainers
**Source:** Anthropic release notes 2026-04-23 ([Memory for Claude Managed Agents, public beta](https://platform.claude.com/docs/en/release-notes/overview#april-23-2026)) and the [Using agent memory](https://platform.claude.com/docs/en/managed-agents/memory) integration guide.

## TL;DR recommendation

**Wait for GA, but ship a thin telemetry adapter now.** Add memory-store reads, writes, deletes, and version churn as countable events behind an optional `agentguard47[anthropic-memory]` extra. Do not promise budget enforcement on memory yet because Anthropic does not publish a token-billing model for memory ops; revisit when memory pricing is documented or when GA lands.

## Why this matters for AgentGuard

AgentGuard's pitch is "runtime guard for any agent: budget, loops, timeouts, rates." Managed Agents Memory introduces a new state surface that lives outside the message-loop AgentGuard already watches. Three concrete blind spots:

1. A misbehaving agent can write thousands of small memories in a tight loop. Today AgentGuard would only see the parent message tokens, not the write churn.
2. Memory content is read back into future sessions as system-prompt context. If an agent silently grows a memory store, future sessions get more expensive in a way the current per-session budget does not catch.
3. Prompt injection into a `read_write` store is now a documented attack surface. AgentGuard already pitches static guards as defense against runaway agents; memory writes are a natural place to add a write-rate guard.

If a customer adopts memory and AgentGuard is silent on it, the "we guard your entire agent budget" claim has a real gap.

## What memory actually is (one paragraph)

A memory store is a workspace-scoped collection of text files mounted into a session at `/mnt/memory/` and accessed with the agent's normal file tools. Stores are created via `POST /v1/memory_stores`; individual memories are created, listed, retrieved, updated, and deleted under `/v1/memory_stores/{id}/memories`. Every mutation produces an immutable memory version under `/v1/memory_stores/{id}/memory_versions`. Stores attach to a session in the `resources[]` array at session-create time with `access` of `read_write` (default) or `read_only`. All endpoints require the `managed-agents-2026-04-01` beta header.

## Documented limits (beta)

| Limit | Value |
| --- | --- |
| Memory stores per organization | 1,000 |
| Memories per store | 2,000 |
| Total storage per store | 100 MB |
| Versions per store | 250,000 |
| Size per memory | 100 kB (~25k tokens) |
| Version retention | 30 days (recent versions kept beyond) |
| Memory stores per session | 8 |
| `instructions` per attachment | 4,096 chars |

## Cost dimensions to model

Anthropic's docs do not publish a separate per-token price for memory reads, writes, or storage in the release notes or the integration guide. So the cost surface AgentGuard should model is a mix of inferred and observed:

| Dimension | What AgentGuard counts | Source of truth | Notes |
| --- | --- | --- | --- |
| `memory.reads` | calls to `memories.retrieve` and `memories.list` | client-side (SDK call site) | proxy for "agent looked at memory" |
| `memory.writes` | calls to `memories.create` and `memories.update` | client-side | catches write loops |
| `memory.deletes` | calls to `memories.delete` | client-side | rare; useful for audit |
| `memory.bytes_written` | sum of `len(content)` across writes | client-side | bounds storage growth |
| `memory.bytes_read` | sum of `len(content)` across retrieves | client-side | catches expensive context bloat |
| `memory.version_churn` | versions created per store per minute | client-side | proxy for "is the agent thrashing?" |
| `memory.tokens_in_prompt` | tokens added to the system prompt by attached stores | server-side, derived from session usage | needs an Anthropic-side number; today we estimate from byte count |
| `memory.store_count_per_org` | gauge against the 1,000 store cap | client-side periodic poll | quota awareness |

The first six are countable today with a small SDK wrapper. The last two need server data we do not currently get in a structured way; treat them as "best-effort" until Anthropic exposes per-session memory token usage in the response.

## How AgentGuard would surface this

### Counter names

Follow the existing AgentGuard naming convention (snake_case, dotted scope, no provider prefix in the counter itself):

```
memory.reads
memory.writes
memory.deletes
memory.bytes_read
memory.bytes_written
memory.version_churn
```

Provider scope is set via the existing `provider` label (e.g., `provider="anthropic-managed-agents"`). This keeps counters portable if OpenAI Codex or Gemini ship a similar surface.

### Budget rules

Three new rule shapes, all opt-in:

1. `max_memory_writes_per_session` — int. Hard cap on writes inside one session.
2. `max_memory_write_rate` — int writes per minute. Catches tight write loops.
3. `max_memory_bytes_per_store` — int. Pre-flight check before a write that would push the store past the threshold (defaults to 90% of the 100 MB ceiling).

Reads are not capped by default. Reading is cheap and the failure mode is "context bloat," which is already covered by AgentGuard's input-token budget rule.

### Default limits

```
max_memory_writes_per_session = 200
max_memory_write_rate         = 60   # per minute
max_memory_bytes_per_store    = 94371840   # 90 MB, 90% of beta ceiling
```

These are conservative and will be re-tuned once we see real workloads. Defaults are off in core; users opt in by importing the extension.

## Packaging: core vs. extra

**Recommendation: ship as `agentguard47[anthropic-memory]` extra.**

Reasoning:

- AgentGuard core is provider-agnostic. Pulling in the Anthropic SDK as a hard dep would break the "model-agnostic runtime guard" framing.
- The existing extras pattern in `sdk/pyproject.toml` already separates `langchain`, `langgraph`, `crewai`, and `otel`. An `anthropic-memory` extra fits the same shape.
- Users who do not use managed agents pay zero install cost.

Sketch:

```toml
[project.optional-dependencies]
anthropic-memory = ["anthropic>=0.39"]
```

Wiring lives at `agentguard/integrations/anthropic_memory.py` and exposes a thin wrapper around the SDK's memory-store calls that emits the counters above before returning.

## Build / wait / punt

**Wait for GA, ship telemetry now.** Implement the six client-side counters and the three opt-in budget rules behind the `anthropic-memory` extra. Do not commit to enforcing dollar-denominated budgets on memory until Anthropic publishes a token-billing model for memory ops or until GA includes per-session memory-token usage in the response. Revisit at GA or at the next Anthropic pricing-page change, whichever comes first.

## Open questions for follow-up

1. Does Anthropic bill memory content read into the system prompt as input tokens at the standard model rate, or is there a separate line item? The docs do not say. A 5-minute test with the usage API can answer this.
2. Will memory-version churn itself ever be billed (e.g., per-write fee)? Today the docs imply no, but worth checking at GA.
3. How does compaction interact with memory? If a session compacts, do attached-store contents get re-injected? This affects how we estimate `memory.tokens_in_prompt`.
4. Do we need a separate counter for `memory_versions.redact` calls? Compliance customers will care; everyone else will not.

## Cross-refs

- Anthropic release notes, 2026-04-23 entry.
- Anthropic docs: "Using agent memory" (`/docs/en/managed-agents/memory`).
- Internal source card: `Knowledge/sources/2026-04-23-claude-managed-agents-memory-beta.md`.
- Internal queue task: `Queue/agent47/memory-telemetry-scope.md`.
