# Inbox Log
**Format:** Newest first. One short entry after each merged PR.

---

## 2026-04-02 | Codex

### What shipped
- Added a small enterprise support section to the public README and generated
  PyPI README.

### Decisions made
- Keep support copy near the bottom of the README, above License, and avoid a
  sales-heavy tone.
- Keep README-facing copy changes synced through the generated PyPI README.

### Blockers
- None.

## 2026-04-02 | Codex

### What shipped
- Standardized `inbox/log.md` as the durable cofounder handoff for the SDK repo.
- SDK instructions now point agents to the inbox log instead of a rolling `latest.md`.
- Official MCP Registry listing is live for `io.github.bmdhodl/agentguard47`.

### Decisions made
- Keep this inbox SDK-only so public repo memory does not leak company strategy.
- Use one terse merged-PR log entry instead of a chat-style running diary.
- Keep the SDK focused on runtime enforcement and coding-agent safety.

### Blockers
- Glama listing is still blocked despite root and package Smithery/Docker metadata.
- `awesome-mcp-servers` PR is waiting on the Glama badge.

## 2026-04-17 | Codex

### What shipped
- Closed stale/noise issues `#343`, `#357`, `#295`, and out-of-scope business issue `#142`.
- Refreshed `mcp-server/package-lock.json` to clear transitive MCP vulnerability findings and merged PR `#358`.

### Decisions made
- Keep scout-run issue noise out of the public SDK backlog when the owning automation does not live in this repo.
- Keep business/outreach work out of the public SDK repository.

### Blockers
- Remaining open issue set is intentional: `#324` (Glama), `#282` (Trusted Publishing), `#279` (Scorecard governance).
