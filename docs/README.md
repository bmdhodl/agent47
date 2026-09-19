# AgentGuard documentation

Install `agentguard47`, import `agentguard`. The repository name is `agent47`.

## Learn with a local run

- [Getting started](guides/getting-started.md): install, run an offline check, and inspect a trace.
- [Enforcement boundary](enforcement-boundary.md): which paths are advisory, recorded-budget preflight, reservation-backed, or unsupported.
- [Runnable examples](../examples/README.md): copy a complete example into your project.

## Complete a task

- [Coding agents](guides/coding-agents.md)
- [Framework starters](../examples/starters/README.md)
- [LangChain](integrations/langchain.md), [LangGraph](integrations/langgraph.md), [CrewAI](integrations/crewai.md)
- [Decision tracing](guides/decision-tracing.md)
- [Managed sessions](guides/managed-agent-sessions.md)
- [Hosted ingest contract](guides/dashboard-contract.md)

## Look up behavior

- [Public API exports](../sdk/agentguard/__init__.py)
- [Guard signatures and defaults](../sdk/agentguard/guards.py)
- [CLI implementation](../sdk/agentguard/cli.py). Run `agentguard --help` for your installed version.
- [Package metadata](../sdk/pyproject.toml) and [changelog](../CHANGELOG.md)
- [Architecture](../ARCHITECTURE.md)

## Contribute and maintain

Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS.md](../AGENTS.md).
Report vulnerabilities through [SECURITY.md](../SECURITY.md).

Change the relevant guide in the same pull request as an API change.
Keep runnable examples small enough to test without keys or paid services.
Link to metadata, source, and dated audits instead of copying release versions,
coverage percentages, or dependency-health claims into each page.

The README example and this index's local links run through
`sdk/tests/test_documentation.py`. Regenerate `sdk/PYPI_README.md` with
`python scripts/generate_pypi_readme.py --write` after editing the root README.
