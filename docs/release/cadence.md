# Release Cadence

AgentGuard has two release tracks:

- `agentguard47` Python SDK on PyPI.
- `@agentguard47/mcp-server` read-only MCP server on npm, MCP Registry, and
  Glama.

Keep these tracks separate. Do not bump the SDK just to fix MCP directory
metadata, and do not publish the MCP package just because the SDK shipped.

## Cadence

| Track | Readiness review | Release target | Release when |
|---|---:|---:|---|
| MCP package and directories | Weekly, Tuesday | Same week if needed | `mcp-server/` code, package metadata, tool schema, environment schema, registry metadata, or Glama indexing needs a refresh |
| Python SDK | Monthly, first release-cadence run of the month | Same week if ready | Runtime behavior, public API, docs, examples, or release proof changed enough that users benefit from a new PyPI version |
| Hotfix | As needed | Same day | Security, broken install, broken publish, broken hosted-ingest contract, or a regression in local guard proof |

A no-release decision is valid. The release issue should say why the train is
held instead of forcing a version bump with no user-visible value.

## MCP Release Train

The MCP release train covers npm, MCP Registry, and Glama. Use
[`mcp-publishing.md`](mcp-publishing.md) for the publish commands.

Weekly readiness checks:

```bash
npm view @agentguard47/mcp-server version
node -p "require('./mcp-server/package.json').version"
npm --prefix mcp-server test
python -m pytest sdk/tests/test_mcp_registry_metadata.py -v
python scripts/sdk_release_guard.py --check-mcp-npm
curl "https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47"
```

Release decision:

- Publish npm when `mcp-server/package.json`, `mcp-server/server.json`, runtime
  tool behavior, or package files changed.
- Republish MCP Registry metadata after the npm package is live whenever public
  registry search lags the current npm package.
- Publish a Glama release after npm and registry verification, using the same
  MCP package version.
- If only Glama indexing is stale, do not change SDK or MCP runtime code. Run
  the Glama build/test/release flow and record the outcome.

Post-release proof:

- npm latest matches `mcp-server/package.json`.
- `npx -y @agentguard47/mcp-server --help` starts.
- MCP Registry search reports the current npm package version.
- Glama public API exposes the environment schema.
- Glama tool pages render all seven tools: `query_traces`, `get_trace`,
  `get_trace_decisions`, `get_alerts`, `get_usage`, `get_costs`, and
  `check_budget`.
- `query_traces` keeps an A-grade rendered score page and states that it is
  read-only, returns a JSON `traces` array, defaults to `limit=20`, and should
  be used to find `trace_id` values before detail calls.

## SDK Release Train

The SDK release train is monthly by default. Patch releases can ship sooner for
hotfixes, but feature releases should wait until there is enough user-visible
value to justify the release.

Monthly readiness checks:

```bash
python scripts/generate_pypi_readme.py --check
python scripts/sdk_release_guard.py
python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py
python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
```

Before tagging:

- `CHANGELOG.md` has a section for the intended SDK version.
- `sdk/pyproject.toml` matches the intended tag.
- `sdk/PYPI_README.md` is regenerated and checked.
- Hosted ingest proof is run when tracing, `HttpSink`, decision events, or the
  dashboard ingest contract changed.
- `ops/03-ROADMAP_NOW_NEXT_LATER.md`, `ops/04-DEFINITION_OF_DONE.md`, and
  `memory/state.md` are reviewed for drift.

After publish:

- GitHub Release exists for the tag.
- PyPI exposes the new version.
- PyPI release files show Trusted Publishing provenance and attestations.
- `pip install agentguard47==<version>` works from a clean environment.
- `agentguard doctor`, `agentguard demo`, and `agentguard quickstart` still run
  without API keys.

## Scheduled Issue

The `Release Cadence` workflow opens or updates one active release queue issue.
It is a reminder and status collector only. It does not publish packages,
create tags, submit registry metadata, or call Glama admin endpoints.

Use the issue to record:

- current SDK version in repo and PyPI
- current MCP version in repo and npm
- Glama tool indexing status
- whether this week's MCP train ships, holds, or needs manual Glama action
- whether this month's SDK train ships, holds, or needs more proof
