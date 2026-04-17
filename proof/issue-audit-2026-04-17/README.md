Issue audit proof for 2026-04-17.

Scope:
- issue #278: vulnerable MCP server transitive dependencies
- stale/noise issue disposition review for #343, #357, #295, and #142

Artifacts:
- `npm-audit.json`: `npm audit --json` after the lockfile refresh
- `mcp-test.txt`: `npm test` output for the MCP server
- `lockfile-diff.txt`: exact lockfile delta showing the transitive dependency refresh

Result:
- `npm audit` reports 0 vulnerabilities
- MCP server build and tests pass
- the only repo code change is the `mcp-server/package-lock.json` refresh
