# SDK State

**Last Updated:** 2026-10-03

- Published package: `agentguard47` 1.4.0, MIT, zero runtime dependencies, Python 3.9+. The next 2.0.0 candidate requires Python 3.11+.
- Latest verified published SDK release: 1.4.0, published 2026-09-24 UTC. Store-backed sync OpenAI calls and store-backed streams reserve before send. PyPI wheel and sdist carry Trusted Publishing attestations from `publish.yml`; a clean install passes `doctor`, `demo`, `quickstart`, and `report`. Receipts: `proof/v1.4.0/PUBLICATION.md`. Earlier receipts: `proof/v1.3.2/PUBLICATION.md`, `proof/v1.3.1/PUBLICATION.md`.
- Current source version: 2.0.0 candidate. The owner-approved Python 3.11 minimum makes this a breaking release and replaces the planned 1.4.1 candidate. It adds `agentguard --version`, `agentguard receipt` (#781), `agentguard hook claude-code` and `agentguard run` (#782), patches the OpenAI Responses API and so the Agents SDK (AG-06, with a separate skip-free OpenAI 1.66.3 / Agents 0.0.3 floor CI job), fixes `AsyncOpenAI`/`AsyncAnthropic` calls that crashed after `init()`, merges the two price tables (Claude rows checked 2026-09-26; OpenAI/Google 2026-07-15), stops `report`, `summarize_trace`, and `receipt` double-counting the call that trips a budget, and carries the restored CrewAI/ChromaDB disclosure. PyPI remains 1.4.0; no 2.0.0 tag or publication is authorized by PR #831. The landing page labels the new commands as 2.0.0 candidate features.
- The Claude Code hook is recorded-event preflight for tool calls that fire `PreToolUse` (tested against Claude Code 2.1.283 on Linux). It does not see tokens, subagent internals, or subscription quota. Cursor, a doctor probe, and Windows/macOS runs remain open under AG-09 (#738).
- Each stable publish now dispatches `published-wheel.yml`, which runs the exact PyPI wheel offline on Windows, macOS, and Linux.
- npm read-only MCP package remains 0.2.2; the local lockfile has been security-audited.
- September audit fixes invalid budget caps, corrupt persisted budgets, callback deadlocks, cross-period payment rollback, DNS rebinding, credential redirects, and swallowed LangChain stops.
- The 2.0.0 candidate and its optional extras require Python 3.11+; dependency floors are unchanged.
- CrewAI remains optional with an explicitly documented unresolved ChromaDB advisory set. Base installs do not include it.
- Release proof belongs in `proof/audit-20260912/` and the versioned release proof folder.
- Public enforcement claims follow [docs/enforcement-boundary.md](../docs/enforcement-boundary.md). Recorded-budget preflight is not an invoice cap or a host interceptor. One store-backed OpenAI path reserves a call before send.
- Public activation counts follow [docs/guides/activation-metrics-design.md](../docs/guides/activation-metrics-design.md). Page views are not installs. `agentguard demo --feedback` is local-only.
- Local reservation is implemented for sync, non-streaming OpenAI Chat Completions and Responses calls, and for OpenAI/Anthropic streams that share a `StateStore`. Contract: [docs/guides/reservation-contract.md](../docs/guides/reservation-contract.md). `check()` / `consume()`, in-memory streams, async non-stream calls, and Anthropic non-stream calls stay recorded-budget preflight. Not an invoice cap.
