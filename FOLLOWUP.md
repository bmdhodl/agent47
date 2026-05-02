# Follow-up

## From PR #404

1. Refresh stale roadmap and architecture docs in a separate hygiene PR.
   - Done in PR `#406`.
   - Keep future ops-doc updates concise and SDK-only.

2. Design opt-in activation metrics before adding any telemetry.
   - No default SDK telemetry.
   - Keep local-only usage private by default.
   - If implemented later, prefer explicit opt-in CLI/reporting metrics only.

3. Keep future demos focused on the strongest SDK wedge.
   - Local proof first.
   - Budget stops, loop stops, retry stops, incident reports.
   - Avoid drifting into broad observability, static scanning, or dashboard-only claims.

## Next Recommended PR

Write a short opt-in activation metrics design note. Do not implement telemetry
yet. The design should define what would be useful to measure, what must never
be collected, where consent would be explicit, and how this stays compatible
with the SDK's zero-dependency, local-first promise.
