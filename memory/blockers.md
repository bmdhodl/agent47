# SDK Blockers

**Last Updated:** 2026-05-08

## Active
- **Glama tool catalog is not indexed yet.** Patrick published the first Glama
  release on 2026-05-08 and the listing is live, but
  `https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47` still returns
  `tools: []`. Recheck before advertising the listing as fully indexed.
- **Official MCP Registry metadata is stale.** npm serves
  `@agentguard47/mcp-server@0.2.2`, but registry search still reports package
  version `0.2.1`. Refresh / republish registry metadata without changing SDK
  runtime code.
- **`awesome-mcp-servers` PR needs the Glama URL.** PR
  `punkpeye/awesome-mcp-servers#4012` can be unblocked with
  `https://glama.ai/mcp/servers/bmdhodl/agent47` once the Glama tool catalog is
  confirmed or Patrick accepts posting the live listing while indexing catches
  up.

## Do Not Route Around
- Do not build new guards just because registry indexing lags.
- Do not put business or consulting workaround plans in this repo.
