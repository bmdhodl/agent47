# Inbox Log
**Format:** Newest first. One short entry after each merged PR.

---

## 2026-04-20 | Codex

### What shipped
- Merged PR `#375` to refresh `ops/00-NORTHSTAR.md` and close ops-cadence issue `#369`.
- Added an explicit public-repo boundary: this repo owns SDK/MCP/local proof/release infrastructure, while dashboard work stays private.

### Decisions made
- Treat the North Star as still accurate, but make the repo boundary visible so future agents do not drift into dashboard work.

### Blockers
- None from this PR.

## 2026-04-20 | Codex

### What shipped
- Merged PR `#372` to fix the release announcement workflow shell quoting bug and close issue `#364`.
- Updated release-status memory/docs now that SDK `v1.2.8` is shipped.

### Decisions made
- Release announcement text must be passed as data via environment variables, temp files, and GraphQL variables instead of interpolated into shell/query strings.

### Blockers
- Remaining open issues are intentional: `#324`, `#282`, and `#279`.

## 2026-04-18 | Codex

### What shipped
- Merged PR `#360` and released SDK `v1.2.8` to PyPI.
- Hardened Scorecard surfaces with hash-locked workflow tool installs, pinned Docker base-image digests, and a 1-review branch-protection rule.

### Decisions made
- Used an explicit admin merge override after owner approval because the new review rule blocked the release PR authored by the same account.
- Kept token-based PyPI publish until the external Trusted Publisher setup is finished.

### Blockers
- Release announcement workflow failed on shell quoting and is tracked in issue `#364`; package publish and GitHub release are complete.
- Remaining open governance/distribution issues are intentional: `#324`, `#282`, `#279`, `#364`, and `#365`.

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

## 2026-04-17 | Codex

### What shipped
- Merged PR `#359` to prep GitHub-side Trusted Publishing for PyPI releases.
- Added the `pypi` GitHub environment and wired `.github/workflows/publish.yml` to use it.

### Decisions made
- Do not remove `PYPI_TOKEN` until the PyPI project owner adds the Trusted Publisher for `bmdhodl/agent47` and `.github/workflows/publish.yml` with environment `pypi`.

### Blockers
- `#282` is still blocked on PyPI project-admin access; repo-side prep is done.

## 2026-04-21 | Codex

### What shipped
- Merged PR `#379` to close P0 issue `#376` by classifying the gitleaks findings as historical placeholder false positives.
- Added scoped `.gitleaksignore` fingerprints and redacted proof artifacts under `proof/gitleaks-376-2026-04-21/`.

### Decisions made
- No credential rotation or history rewrite: the finding was the dummy placeholder `ag_live_abc123`, not a provider-issued secret.

### Blockers
- None for `#376`; issue is closed.
