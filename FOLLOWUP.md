# Follow-up

## From PR #404

1. Refresh stale roadmap and architecture docs in a separate hygiene PR.
   - Done in PR `#406`.
   - Keep future ops-doc updates concise and SDK-only.

2. Design opt-in activation metrics before adding any telemetry.
   - Done in `docs/guides/activation-metrics-design.md`.
   - No default SDK telemetry.
   - Keep local-only usage private by default.

3. Keep future demos focused on the strongest SDK wedge.
   - Local proof first.
   - Budget stops, loop stops, retry stops, incident reports.
   - Avoid drifting into broad observability, static scanning, or dashboard-only claims.

## Next Recommended PR

Reassess the remaining open issues and pick the next smallest SDK-only unblocker.
Prefer issue `#392` if release announcement reliability still matters, or leave
deferred security/governance issues alone until their phase-2 blockers clear.
