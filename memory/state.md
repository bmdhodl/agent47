# SDK State

**Last Updated:** 2026-09-12

- Public package: `agentguard47`, MIT, zero runtime dependencies, Python 3.9+.
- Latest verified published SDK release: 1.2.13. Security release preparation is in progress.
- Current source version: 1.2.14, never published. The next release will include its accumulated changes.
- npm read-only MCP package remains 0.2.2; the local lockfile has been security-audited.
- September audit fixes invalid budget caps, corrupt persisted budgets, callback deadlocks, cross-period payment rollback, DNS rebinding, credential redirects, and swallowed LangChain stops.
- LangChain/LangGraph extras require Python 3.10+ and tested current floors.
- CrewAI remains optional with an explicitly documented unresolved ChromaDB advisory set. Base installs do not include it.
- Release proof belongs in `proof/audit-20260912/` and the versioned release proof folder.
