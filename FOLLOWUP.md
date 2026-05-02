# Follow-up

## From PR #404

1. Refresh stale roadmap and architecture docs in a separate hygiene PR.
   - `ops/03-ROADMAP_NOW_NEXT_LATER.md` was 2 weeks old during the PR.
   - `ops/02-ARCHITECTURE.md` was 3 weeks old during the PR.
   - Keep this as repo hygiene; do not turn it into feature expansion.

2. Design opt-in activation metrics before adding any telemetry.
   - No default SDK telemetry.
   - Keep local-only usage private by default.
   - If implemented later, prefer explicit opt-in CLI/reporting metrics only.

3. Keep future demos focused on the strongest SDK wedge.
   - Local proof first.
   - Budget stops, loop stops, retry stops, incident reports.
   - Avoid drifting into broad observability, static scanning, or dashboard-only claims.

## Next Recommended PR

Refresh the stale roadmap and architecture docs so they match the current
runtime-control positioning, v1.2.9 package state, MCP listing state, and recent
local-proof additions.
