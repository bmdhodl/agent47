# MCP Package Publishing

Use this checklist when `mcp-server/package.json` is ahead of the public npm
package.

The MCP package is separate from the Python SDK release:

- Python SDK: `agentguard47` on PyPI
- MCP server: `@agentguard47/mcp-server` on npm

## Pre-publish checks

Run from the repo root:

```bash
npm view @agentguard47/mcp-server version
node -p "require('./mcp-server/package.json').version"
npm --prefix mcp-server test
python -m pytest sdk/tests/test_mcp_registry_metadata.py -v
python scripts/sdk_release_guard.py
```

Then verify the package tarball from `mcp-server/`:

```bash
cd mcp-server
npm pack --dry-run
npm publish --dry-run --access public
```

The dry run should show the expected version and only the `dist/`, `README.md`,
`LICENSE`, and `package.json` package files.

## Publish

The npm account must have publish rights and may require a one-time password:

```bash
cd mcp-server
npm publish --access public --otp <one-time-code>
```

Do not store the OTP in shell history, docs, `.npmrc`, or repo files.

## Post-publish verification

```bash
MCP_VERSION="$(node -p "require('./mcp-server/package.json').version")"
npm view @agentguard47/mcp-server version
npm view "@agentguard47/mcp-server@$MCP_VERSION" version
npx -y @agentguard47/mcp-server --help
```

If the latest npm version still does not match `mcp-server/package.json`, stop
and record the exact npm error in a GitHub issue instead of changing SDK
runtime code.
