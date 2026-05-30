# SDK Blockers

**Last Updated:** 2026-05-30

## Active
- **Glama tool catalog is not indexed yet.** Patrick published the first Glama
  release on 2026-05-08 and the listing is live. Glama renders tool and score
  pages, but `https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47` still
  returns `tools: []`. Recheck before relying on the API for tool inventory.
- **Glama related servers need manual submission.** `glama.json` only claims
  maintainers. Related servers are added through the Glama UI; use the
  candidates in `docs/launch/distribution-execution.md`.
- **Official MCP Registry metadata is stale.** npm serves
  `@agentguard47/mcp-server@0.2.2`, but registry search still reports package
  version `0.2.1`. Refresh / republish registry metadata without changing SDK
  runtime code.
- **`awesome-mcp-servers` PR needs the Glama URL.** PR
  `punkpeye/awesome-mcp-servers#4012` can be unblocked with
  `https://glama.ai/mcp/servers/bmdhodl/agent47` once the Glama tool catalog is
  confirmed or Patrick accepts posting the live listing while indexing catches
  up.

## Resolved / Historical
- **`v1.2.13` published successfully.** GitHub Release `v1.2.13` and PyPI
  `agentguard47==1.2.13` are public as of 2026-05-30.
- **`v1.2.12` is a stale failed release tag.** The tag was pushed from
  `8fd0295db19333d882bffed6002e18ea24fadec3`, a checkout whose
  `sdk/pyproject.toml` still says `1.2.10`. The publish workflow authenticated
  and reached PyPI, then failed because it tried to upload existing
  `agentguard47-1.2.10` files. Do not rerun or reuse `v1.2.12`.
- **`v1.2.11` is also stale.** The tag workflow passed release gates, build, and
  attestation, then failed at PyPI with `invalid-publisher` for
  `repo:bmdhodl/agent47:environment:pypi`. It has no PyPI release and no GitHub
  Release.

## Do Not Route Around
- Do not build new guards just because registry indexing lags.
- Do not put business or consulting workaround plans in this repo.
