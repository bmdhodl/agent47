# Inbox Log

## 2026-09-26 | Claude Code | PR #786

- Shipped: `patch_openai` / `patch_openai_async` (and `init()`, `run`) cover the OpenAI Responses API, so the Agents SDK `Runner` stops before its next model call once the budget is spent. Fixed every `AsyncOpenAI`/`AsyncAnthropic` call crashing after `init()`. Raw sync calls with a store reserve (Codex review).
- Decisions: Responses API and Agents SDK are Experimental in the compatibility matrix; the openai floor (1.40.0) predates Responses. `openai-agents` joins the latest compat lock only. Hosted tools, `background=True`, and WebSocket stay unsupported.
- Blockers: None. Reasoning tokens are still billed on top of output tokens; queued separately. `claude-review` hit its 300s timeout on three intermediate heads of this large diff.

## 2026-09-26 | Claude Code | PR #784

- Shipped: Landing page rebuilt as a case file from the new `docs/site-design.md`: real `agentguard receipt` output in the hero, dossier cards for the four stops, three ways in, rules of engagement. Two color tokens raised to pass 4.5:1.
- Decisions: Owner merged before the 1.4.1 release; `hook`, `run`, and `receipt` are labeled "new in 1.4.1". Privacy and JSONL copy qualified after Codex review.
- Blockers: None. Page and PyPI differ until 1.4.1 ships.

## 2026-09-26 | Claude Code | PR #782

- Shipped: `agentguard hook claude-code` refuses the third identical tool call in a row, a call that already failed twice, and calls past `--max-calls`; tested against real Claude Code 2.1.283. `agentguard run` runs an unmodified script with OpenAI/Anthropic patched. Receipt fixes for LangChain traces from Codex review on #781.
- Decisions: Hook state lives in a self-ignoring `.agentguard/claude-code/`, one file per session. Unreadable hook input fails open with a visible error. Settings go to `.claude/settings.local.json`.
- Blockers: Cursor adapter, doctor probe, and Windows/macOS hook runs are still open under AG-09 (#738).

## 2026-09-26 | Claude Code | PR #781

- Shipped: `agentguard receipt <trace.jsonl>` prints each guard stop, recorded cost, and the trace SHA-256 as a barcode. `--format markdown` for PRs, `json` for CI. ASCII barcode when stdout cannot encode blocks.
- Decisions: The hash identifies the trace; it is not a signature. The showwork join stays with AG-14 (#743). Guard events do not add cost.
- Blockers: `agentguard report` still double-counts the tripping call's cost; queued separately.

## 2026-09-25 | Claude Code | PR #779

- Shipped: Site redesign on one shared stylesheet. Copy scores 0.000 on the slop scan. The compare snippet now passes `budget_guard=`; the old one never stopped. A site test rejects any `patch_*` example without it.
- Decisions: Removed the unsourced 340% stat, stale competitor pricing, and absolute trust claims. The hosted dashboard UI is in the private repo.
- Blockers: Codex review errored twice on its side; Cursor Bugbot is over its usage limit.

## 2026-09-25 | Claude Code | PR #778

- Shipped: The Claude review diff omits generated lockfiles and showwork snapshots, and lists them by name.
- Decisions: A section is dropped only when every path in it is generated.
- Blockers: None.

## 2026-09-25 | Claude Code | PR #777

- Shipped: AG-07 compat CI job. The full suite runs against real OpenAI, Anthropic, LangChain, LangGraph, and OTel packages at floor and latest; a missing package fails. `docs/compatibility.md` publishes the matrix and support policy.
- Decisions: CrewAI stays Experimental (#644); Responses API stays Unsupported (AG-06). Async/streamed provider calls are marked stand-ins only.
- Blockers: none. Dependabot's weekly `compat-latest.txt` refresh is the early warning.

## 2026-09-25 | Claude Code | PR #776

- Shipped: `agentguard --version` exits 0; source bumped to 1.4.1.
- Decisions: Owner held the tag; release is scheduled for 2026-10-01.
- Blockers: none.

## 2026-09-25 | Claude Code | PR #775

- Shipped: Recorded 1.4.0 as published: `memory/state.md`, `proof/v1.4.0/PUBLICATION.md` (PyPI attestations, clean install, Windows/macOS/Linux run 36190628659), roadmap and follow-ups.
- Decisions: No docs-only release. The next release waits for an SDK change.
- Blockers: `agentguard --version` exits 2 and needs owner approval to add.

## 2026-09-25 | Claude Code | PR #774

- Shipped: AG-17 repo slice. `publish.yml` dispatches `published-wheel.yml`, which runs the exact PyPI wheel offline on Windows, macOS, and Linux. First v1.4.0 run passed 4/4.
- Decisions: Dispatch only, no schedule, so no recurring clone noise.
- Blockers: Outside testers and a PowerShell walkthrough still need people.

## 2026-09-25 | Claude Code | PR #773

- Shipped: AG-19 repo slice. CONTRIBUTING has a one-session provider usage fixture path; a doc test runs its snippets.
- Decisions: The example asserts token buckets and table cost, not only the source.
- Blockers: Posts, 7/14-day readbacks, and outside reports need the owner.

## 2026-09-25 | Claude Code | PR #764

- Shipped: `next-ticket` skill for Claude, Cursor, Codex, and Copilot.
- Decisions: It follows #729's ordered sequence and skips held tickets such as AG-06.
- Blockers: None.

## 2026-09-25 | Claude Code | PR #760

- Shipped: Owner TLDR after every merge; inbox entries for #758 and #759.
- Decisions: Process only.
- Blockers: None.

## 2026-09-25 | Claude Code | PR #762

- Shipped: Inbox entry for the AG-03 merge (#761).
- Decisions: Inbox only.
- Blockers: None.

## 2026-09-25 | Claude Code | PR #724

- Shipped: Restored the ChromaDB advisory disclosure for the optional CrewAI extra in README, PyPI README, and the CrewAI guide.
- Decisions: Base installs are unaffected; tracked in #644.
- Blockers: PyPI shows it only after the next release.

## 2026-09-25 | Claude Code | PR #728

- Shipped: Scorecard fixes: pinned eval action, hashed MCP budget deps, Claude review diff over the GitHub API with visible CLI errors.
- Decisions: CI now fails if `mcp-budget.in` drifts from `agentguard-mcp` deps.
- Blockers: Fuzzing, CII, Signed-Releases remain; see FOLLOWUP.

Also closed `#767`: #735 (AG-06) is open and held.

## 2026-09-25 - AgentGuard release distribution

- Agent: OpenAI | GPT-6 | auto.
- Shipped: PR #772 verifies the published PyPI wheel demo and report before email; adds an offline example guide and voluntary feedback prompt.
- Decisions: retain existing release page, subscriber service, campaign key, and read-only workflow token. No SDK version change or historical resend.
- Validation: 1,178 SDK tests, 91.49% coverage; 11 MCP tests; published 1.4.0 example and three-width email rendering passed.
- Blockers: none for the merged change. Optional Claude review failed before producing output; Codex review completed without findings, Cursor security and approval passed.

**Format:** Newest first. One short entry after each merged PR.

---

## 2026-09-21 | Cursor

- Merged PR `#761` (AG-03 / #732). Local reservation contract: reserve before send, commit real usage, cancel only if the request never left, otherwise keep the hold. Private model and tests. `BudgetGuard` still overshoots.
- Decision: an unknown provider outcome cannot silently free funds. This is not an invoice cap.
- Blocker: AG-04 / #733 is not started.
- Sign-off: Cursor | Grok 4.7 | auto

## 2026-09-20 | Cursor

- Merged PR `#759` (AG-02): honest activation evidence plus local `agentguard demo --feedback`. Page navigation is not an install. Guard activation is successful consented demo feedback only. Landing-page `install_intent` on 2026-09-18 is proven installs: 0.
- Decisions: no hidden telemetry, no public `__all__` growth, `--omit` stays `nargs="+"`, failed/undifferentiated feedback is unknown not activation. `bmdpat` classifier stays a linked follow-up, not this repo.
- Blockers: none for AG-02. Do not start AG-03 unless asked. No tag or PyPI publish from this PR.
- Sign-off: Cursor | Grok 4.6 | auto

## 2026-09-20 | Cursor

- Merged PR `#758` (AG-01): public enforcement claims now follow `docs/enforcement-boundary.md`. Exhausted recorded budgets refuse the next patched OpenAI Chat Completions / Anthropic Messages dispatch. That is not a concurrent reservation, invoice cap, or host interceptor.
- Decisions: installing the package does nothing to Cursor/Claude Code/Copilot/Codex until app code calls the SDK. Keep overbroad savings/kill-switch copy out of README and site.
- Blockers: none for AG-01. Showwork AG-01 session stayed blocked on undeclared-file gaps; do not rewrite that ledger.
- Sign-off: Cursor | Grok 4.6 | auto

## 2026-09-18 | Cursor

- Merged PR `#725` and tagged `v1.3.2`. OpenAI/Anthropic sync and async streams now bill final usage once. Same mocked stream: 0 tokens on 1.3.1, 200 tokens and one consume on 1.3.2.
- Fresh PyPI wheel, eight CLI paths, build attestation, and GitHub Release passed. Copy still scores 0.0 on Defluff. LinkedIn/X were not posted from this environment. Receipts: `proof/v1.3.2/PUBLICATION.md`.
- Concurrent reservations, predicted response cost, and optional CrewAI/ChromaDB issue 644 remain outside this fix. The PR 726 subscriber email job was not in the tag tree; re-run Release Content on `v1.3.2` from current main.
- Sign-off: Cursor | Grok 4.6 | auto

## 2026-09-14 | Codex

- AgentGuard 1.3.1 shipped after PR 721: exhausted recorded budgets now stop OpenAI/Anthropic sync and async requests before dispatch. A one-call budget sends one mocked request across three attempts, versus three on 1.3.0.
- Fresh PyPI install, eight CLI paths, build attestation, 992 tests, and published LinkedIn/X image readbacks passed. Copy and image text scored 0.0 on Defluff. Receipts: `proof/v1.3.1/PUBLICATION.md`.
- Concurrent reservations, streaming totals, and optional CrewAI/ChromaDB issue 644 remain outside this fix. Signup capture is not adoption proof.
- Sign-off: OpenAI | GPT-6 | auto

## 2026-05-31 | Codex

### What shipped
- Merged PR `#559` to harden release publishing against stale git tags.
- `scripts/sdk_release_guard.py` now rejects a release tag when `GITHUB_REF` does not match `sdk/pyproject.toml`.

### Decisions made
- Keep the existing workflow-level tag check, and mirror the invariant in the Python release guard so local and CI checks fail before package build/upload.

### Blockers
- None. The failed `v1.2.12` publish run was a stale tag pointing at `1.2.10`; `v1.2.13` is already published and main CI, CodeQL, and Scorecard passed after `#559`.

## 2026-05-30 | Claude

### What shipped
- Merged PR `#553`: added a shared `STAR_CALL_TO_ACTION` to `doctor`/`demo` output and the README/PyPI README to convert silent installs into GitHub stars (downloads in the thousands vs 3 stars).
- Refreshed `memory/state.md` and `memory/blockers.md` now that `1.2.13` is live on PyPI; deleted the stale dead tags `v1.2.11`/`v1.2.12` from the remote (SHAs recorded for recovery).
- Proof under `proof/star-cta-activation/`; ruff clean, 773 tests pass, PyPI README in sync, release guard passes.

### Decisions made
- Star CTA lives only in human-readable CLI output; `doctor --json` deliberately omits it (test-enforced).
- MCP Registry metadata is staged at `0.2.2`; the remaining publish is the credentialed `mcp-publisher` step, not a code change.

### Blockers
- Glama still returns `tools: []` (UI-gated); `awesome-mcp-servers#4012` was closed and needs a fresh guideline-clean PR.

## 2026-05-30 | Codex

### What shipped
- Merged PR `#550` and published `agentguard47==1.2.13` to PyPI.
- GitHub Release `v1.2.13` and release-content workflow completed successfully.
- Added release proof under `proof/release-v1.2.13/` and verified a clean PyPI install through `doctor`, `demo`, `quickstart --write`, generated quickstart run, and `report`.

### Decisions made
- Treat `v1.2.11` and `v1.2.12` as stale failed release tags; do not rerun or reuse them without explicit owner approval.
- Tag future releases only after proving the tag target's `sdk/pyproject.toml` version matches the tag.

### Blockers
- None.

## 2026-05-29 | Codex

### What shipped
- Merged PR `#548` to prepare SDK release candidate `v1.2.12`, update release docs/metadata, and harden release notes so failed raw tags do not truncate public GitHub Release notes.

### Decisions made
- Treat `v1.2.11` as a stale failed tag with no PyPI publish and no GitHub Release.
- Track `v1.2.12` as a release candidate until PyPI Trusted Publishing succeeds.

### Blockers
- PyPI Trusted Publishing must be configured for `agentguard47` with owner `bmdhodl`, repo `agent47`, workflow `publish.yml`, and environment `pypi` before tagging `v1.2.12`.

## 2026-05-02 | Codex

### What shipped
- Merged PR `#412` to make release announcement discussion creation skip safely
  when GitHub Discussions categories are unavailable.
- Closed issue `#392`; release-adjacent automation no longer fails on missing
  Discussions configuration.

### Decisions made
- Keep deferred phase-2 governance/security issues tracked in GitHub instead of
  duplicating them in `ops/FOLLOWUP.md`.

### Blockers
- `#282` and `#279` remain intentionally deferred phase-2 work.

## 2026-05-02 | Codex

### What shipped
- Merged PR `#408` to add a docs-only opt-in activation metrics design.
- Documented allowed questions, explicit consent boundaries, forbidden fields,
  zero-dependency transport constraints, and no-default-telemetry non-goals.

### Decisions made
- Keep SDK activation metrics as design-only unless explicitly approved later.
- Prefer server-side/package metrics before any local SDK telemetry.

### Blockers
- None.

## 2026-05-02 | Codex

### What shipped
- Merged PR `#406` to refresh stale SDK roadmap and architecture docs.
- Updated current focus around `v1.2.9`, official MCP Registry listing,
  dashboard contract boundaries, decision traces, and local proof surfaces.

### Decisions made
- Keep ops docs SDK-only and concise.
- Treat remote kill as a documented dashboard boundary, not an SDK behavior
  claim.
- Keep repo-only examples distinct from package-installed CLI proof paths.

### Blockers
- None.

## 2026-05-02 | Codex

### What shipped
- Merged PR `#404` to add a local coding-agent review-loop proof.
- Added `examples/coding_agent_review_loop.py`, docs links, PyPI README sync,
  focused regression coverage, proof artifacts, and `ops/FOLLOWUP.md`.

### Decisions made
- Keep activation work focused on local runtime proof: budget stops, retry
  stops, and incident reports.
- Track stale roadmap/architecture refresh in `ops/FOLLOWUP.md`; the
  activation-metrics design is now captured as a docs-only step, not SDK
  telemetry.

### Blockers
- None.

## 2026-05-01 | Codex

### What shipped
- Merged PR `#402` to add a sourced Uber AI-budget overrun datapoint to the README and generated PyPI README.
- Captured docs validation proof under `proof/queue-uber-readme-2026-05-01/`.

### Decisions made
- Kept this as SDK positioning only: no runtime behavior changes, no dashboard work, and no unsupported claims beyond the cited Briefs report.

### Blockers
- None for the Uber README queue item.

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

## 2026-04-25 | Codex

### What shipped
- Merged PR `#390` to align SDK decision traces and docs with the hosted dashboard ingest contract.
- Staged SDK release `v1.2.9` with release metadata, generated PyPI README, and validation proof.

### Decisions made
- Keep the SDK local-first: hosted ingest mirrors events, but local guards remain the authoritative runtime stop path.
- Keep new dashboard-contract guide links on `main` in generated PyPI README until the release tag contains the new guide.

### Blockers
- None.

## 2026-05-02 | Codex

### What shipped
- Merged PR `#415` to tighten the SDK activation path: clearer README quickstart, copy-paste local setup, and a shareable coding-agent review-loop incident artifact.
- Added tests that keep the sample incident and PyPI README links in sync.

### Decisions made
- Keep activation proof local-first and zero-network by default.
- Describe hosted ingest as retained alerts and team-visible follow-up, not as a remote kill switch by itself.

### Blockers
- None.

## 2026-05-02 | Codex

### What shipped
- Released SDK `v1.2.10` to PyPI and created the GitHub Release.
- Included activation proof docs, review-loop incident proof, PyPI README sync, and release-build timestamp hardening.

### Decisions made
- Keep this as a patch release focused on activation/distribution and release reliability.
- Continue using `PYPI_TOKEN` until PyPI Trusted Publishing is configured by the package owner.

### Blockers
- None for `v1.2.10`; PyPI Trusted Publishing remains a known follow-up.

2026-09-12 | OpenAI GPT-6 auto | Merged #710: restored generated README checks and moved price-age reminders out of deterministic tests. SDK audit and security release in progress.
