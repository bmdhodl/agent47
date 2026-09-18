# Release subscriber email

Every published stable SDK version triggers the independent `email` job in
`.github/workflows/release-content.yml`. The PyPI publish workflow already
explicitly dispatches that workflow after creating the GitHub release, because
GitHub-token-created release events do not trigger another workflow.

The sender checks that the exact tag is a published, non-prerelease GitHub
release and the matching PyPI version exists and is not yanked. The email links
to that release's notes and includes the pinned upgrade command. Prereleases do
not send. Discussion failures do not block the email job.

bmdpat owns subscriber selection, unsubscribe links, suppression, the complaint
pause, rendering, and Resend delivery. No subscriber data or provider credential
is stored in this public repository. The only sender secret is
`AGENTGUARD_RELEASE_API_KEY`, also configured in bmdpat. That key can only target
the AgentGuard cohort. bmdpat's `AGENTGUARD_RELEASE_MODE=live` enables sending;
`off` disables it independently of the weekly newsletter.

Owner authorization: Patrick requested automatic emails to AgentGuard subscribers
for every software release on 2026-09-18. The existing weekly newsletter approval
policy remains in effect for weekly issues.

## Verify without sending

Run the Release Content workflow with the existing published tag and
`email_dry_run=true`. Its email job validates the artifacts and eligible audience,
returning counts only. It writes no delivery claims and sends no email. The
other announcement job is skipped for this dry run.

## Retry and delivery proof

Rerun a failed email job with the same tag. The service derives the stable
campaign key `agentguard-release:vMAJOR.MINOR.PATCH`. The existing database claim
and Resend idempotency key prevent repeated accepted sends, including after a
workflow retry. Do not change that key to force a resend. In-flight or ambiguous
claims fail the job for operator reconciliation instead of claiming success.

Actions logs expose only counts. Provider acceptance is not delivery: inspect
`subscriber_email_deliveries` for that campaign and Resend delivery webhooks.
Unsubscribed, suppressed, and fixture addresses remain excluded. An empty cohort
is a successful zero-recipient send. New subscribers are included on subsequent
releases. This pipeline change does not backfill old release announcements.
