# Repo health - 2026-05-27 run7

## Identity

- Repo: `bmdhodl/agent47`
- Local checkout: `<repo>`
- Branch: `dogfood-2026-05-27-run7-worker`
- Base commit: `3f54935`

## Staleness

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: `3 weeks ago`
- `ops/02-ARCHITECTURE.md`: `4 weeks ago`

Both exceed the AGENTS.md thresholds. Issue #473 already tracks this, so this
run did not create another staleness issue.

## Open PR sweep

Most open PRs are blocked by required human review, not failing local proof.
Checked review threads for #526, #525, #524, #523, #520, #519, #508, and #476.

- #526: green/review-required, no active unresolved review threads found.
- #525: green/review-required, no active unresolved review threads found.
- #524: green/review-required, no active unresolved review threads found.
- #523: green/review-required, no active unresolved review threads found.
- #520: review-required with 6 active unresolved review threads about release workflow ordering, release-note labels, and prerelease documentation.
- #519: review-required, no active unresolved review threads found.
- #508: review-required; still the highest-ROI dependency PR to fix next because prior runs identified the setup-go guardrail expectation mismatch.
- #476: merge-conflicted (`DIRTY`), no active unresolved review threads found.

No PR was merged because none was approved.

## Open issues

- #490 remains the rolling dogfood proof log.
- #473 remains the active ops freshness tracker.
- #507 and #469 remain security/dependency audit trackers.
- #512 through #515 still look like tech-debt scanner noise from docs/proof artifacts and need triage.
- #418 remains the weekly dependency drift tracker.

## Release and distribution snapshot

- GitHub release: `v1.2.10`
- PyPI latest: `agentguard47==1.2.10`
- npm MCP package: `@agentguard47/mcp-server@0.2.2`
- Local MCP metadata: `mcp-server/package.json` and `mcp-server/server.json` both report `0.2.2`
- Official MCP Registry search still reports `0.2.1`
- Glama API still returns `tools: []`

## Recommended next task

Address PR #520 release-workflow review comments or PR #508 setup-go guardrail
expectation mismatch before adding more proof-only PRs. The proof queue is
already deep and mostly waiting on human review.
