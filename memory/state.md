# SDK State

**Last Updated:** 2026-09-18

- Public package: `agentguard47`, MIT, zero runtime dependencies, Python 3.9+.
- Latest verified published SDK release: 1.3.2, published 2026-09-18 UTC. Fresh PyPI wheel install, eight CLI paths, installed streaming demo (200 tokens, one consume), and wheel build attestation pass. Receipts: `proof/v1.3.2/PUBLICATION.md`.
- Current source version: 1.3.2. OpenAI/Anthropic sync and async patches record final streamed usage once and still reject exhausted recorded budgets before dispatch. Published 1.3.1 receipts remain in `proof/v1.3.1/PUBLICATION.md`.
- npm read-only MCP package remains 0.2.2; the local lockfile has been security-audited.
- September audit fixes invalid budget caps, corrupt persisted budgets, callback deadlocks, cross-period payment rollback, DNS rebinding, credential redirects, and swallowed LangChain stops.
- LangChain/LangGraph extras require Python 3.10+ and tested current floors.
- CrewAI remains optional with an explicitly documented unresolved ChromaDB advisory set. Base installs do not include it.
- Release proof belongs in `proof/audit-20260912/` and the versioned release proof folder.
