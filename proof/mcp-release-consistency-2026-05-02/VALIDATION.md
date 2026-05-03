# MCP Release Consistency Validation

## Scope

MCP package release-infra only. No Python SDK runtime behavior, public SDK API,
dashboard code, hosted ingest contract, or dependencies changed.

Changed:

- `mcp-server/package.json`
- `docs/release/mcp-publishing.md`
- `scripts/sdk_preflight.py`
- `sdk/tests/test_sdk_preflight.py`
- `CHANGELOG.md`

## Verified State

```text
node -p "require('./mcp-server/package.json').version"
0.2.2

npm view @agentguard47/mcp-server version
0.2.1

npm view @agentguard47/mcp-server@0.2.2 version
E404: @agentguard47/mcp-server@0.2.2 is not in this registry.
```

Repo metadata, lockfile, runtime version, and MCP registry metadata all target
`0.2.2`; npm is the stale surface.

## Publish Attempt

`npm publish --access public` was attempted from `mcp-server/` after successful
test and dry-run packaging. npm blocked the publish with:

```text
npm error code EOTP
npm error This operation requires a one-time password from your authenticator.
```

The external fix is:

```bash
cd mcp-server
npm publish --access public --otp <one-time-code>
```

Follow-up issue: https://github.com/bmdhodl/agent47/issues/428

## Checks

```text
npm --prefix mcp-server test
5 passed.

python -m pytest sdk\tests\test_mcp_registry_metadata.py -v
4 passed.

python -m pytest sdk\tests\test_sdk_preflight.py sdk\tests\test_mcp_registry_metadata.py -v
13 passed.

python -m ruff check scripts\sdk_preflight.py sdk\tests\test_sdk_preflight.py
All checks passed.

python scripts\sdk_release_guard.py
Release guard passed.

python scripts\sdk_preflight.py
All checks passed. MCP edits now run `npm.cmd --prefix mcp-server test` on Windows.

cd mcp-server
npm pack --dry-run
Tarball version: @agentguard47/mcp-server@0.2.2.

cd mcp-server
npm publish --dry-run --access public
Dry run passed.
```
