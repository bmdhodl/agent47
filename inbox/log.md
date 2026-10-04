# Inbox Log

2026-10-03 | OpenAI GPT-6 auto | Merged #826 (c0fcbdd), approved #736 Responses/Agents minimum CI: separate hash-pinned OpenAI 1.66.3 / Agents 0.0.3 job on Ubuntu/Python 3.12; both real dispatch and free-client result groups must run without skips and the required aggregate includes responses-floor. Chat 1.40.0 and current matrix remain. Local aggregate: 32 red then 49 passes; two-result XML guard: 16 cases; full SDK: 1583 passed, 3 existing optional skips, zero warnings, 92.56% coverage. Actual Linux floor: 21 Responses/Agents plus 71 free-client passes, zero skips/errors/failures/warnings. Actual Copilot/Codex source review and final Claude review cleared the change; final PR and main code CI, CodeQL, scanner, actionlint and Scorecard pass. Exact archive: 31/31 artifact checks, 20 manifest entries equal Git blobs. Proof: proof/responses-floor-ci-736/. Main's GitHub-generated Dependency Graph scan of CI requirements fails because its updater rejects the existing Python 3.9 tool target; GitHub refuses retry, tracked #827. Keep SDK/tool 3.9 support and security settings intact pending an approved supported submission path. #736 remains open for CrewAI/#644 and parent gates. Candidate 1.4.1 unpublished; zero open PRs, 26 remaining issues with gates.

2026-10-03 | OpenAI GPT-6 auto | Merged #825 (70bef0d), closes #817: owner-approved exact-client free billing on sync/async OpenAI patches and init; paid estimates and token/call limits remain. Review regressions fixed missing-usage zero accounting, unsupported owner identity, atomic exhausted-dollar refusal and zero-cost provenance with unresolved holds retained. Final source: 1552 passed, 3 existing optional skips, zero warnings, 92.54% coverage; installed Windows floor/current wheel profiles 49/71/71 passes, zero skips, all 51 modules and metadata match. Actual final Copilot source review cleared acb81dd; all PR and five main workflows pass. Exact archive: 102/102 artifact checks, 78 manifest entries equal Git blobs. Current proof: proof/free-local-clients-817/review-r3/. Candidate 1.4.1 remains unpublished. Next authorized work: #736 Responses/Agents floor CI; CrewAI and outside-adoption gates remain.

## 2026-09-27 | Claude Code | PR #804

- Shipped: the public live-cost logs no longer show org-wide OpenAI spend. The D-2 report prints billed/table ratios only; other models in the window print as a count; same-model org traffic shows as `>N` with the cost redacted; the artifact carries only the report and this run's trace. First CI run with secrets (dispatch on main) passed the gate on all three models.
- Decisions: the gate still fails on same-model org traffic, since it cannot be told apart from a miscount.
- Blockers: None.

## 2026-09-27 | Claude Code | PR #802

- Shipped: `scripts/live_cost_reconcile.py` and the nightly `live-cost-check.yml` make 6 real OpenAI calls (Chat, Responses, stream, gpt-5-nano minimal, a cached prompt twice) and gate on OpenAI's Usage API. Per model, requests and input/cached/output tokens matched exactly, and recorded cost equals OpenAI's counts x the price table within 1e-9. No SDK change needed.
- Decisions: the job waits up to 60 min (timeout 75) because OpenAI usage for one run's gpt-4.1-nano calls lagged ~55 min. Isolation is by the run's own minute window, gating only the models the run called. The D-2 Costs API check is report-only; this org's cost rows all read $0.00.
- Blockers: the nightly job skips until the owner adds the `OPENAI_API_KEY` and `OPENAI_ADMIN_KEY` Actions secrets.

## 2026-09-26 | Claude Code | PR #800

- Shipped: OpenAI and Gemini rows match their pricing pages (read 2026-09-26). GPT-6, GPT-5.6, gpt-5, gpt-4.1, o3, o4-mini and Gemini 3.x now have rows (they were overestimated 15x to 81x); o1-pro ($150 / $600) was under-billed about 5x at the old $30 / $180 ceiling and now has its own row; cached-input rates for gpt-5.5, gpt-5.4 and Gemini 2.5 fixed. Gemini 3.6-3.8 Flash double on 2027-01-01. Gemini thinking is billed as output, and Gemini cache reads come out of the prompt count. Four live OpenAI calls (Responses, stream, Chat Completions, Agents SDK) recorded the published price exactly.
- Decisions: o1-pro ($150 / $600) is now the ceiling for unknown OpenAI models (fail-closed). Google stays off the ceiling because its image output ($120/1M) is above every text row.
- Blockers: None. Not modelled: OpenAI Fast mode, the residency/FedRAMP uplift, Batch/Flex, Gemini audio/image, and GPT-5.6 Sol after its promo (in `ops/FOLLOWUP.md`).

## 2026-09-26 | Claude Code | PR #797

- Shipped: `_extract_cost` docstring warns that on `guard.budget_exceeded` it returns the `data.cost_usd` echo of a cost already on the tripping call; trace totals must use `_sum_cost` (or `_spend_cost` per event). No behavior change.
- Decisions: Docs only; closes the #783 follow-up.
- Blockers: None.

## 2026-09-26 | Claude Code | PR #783

- Shipped: `report`, `summarize_trace`/`incident`, `assert_cost_under`, and `receipt` count the call that trips a budget once. `guard.budget_exceeded` echoes that call's cost in `data.cost_usd`; one rule (`_spend_cost`) now ignores that echo but keeps a top-level guard `cost_usd`. Real-client repro: report $7.50 -> $6.00, matching the guard.
- Decisions: Guard events that repeat a cost must keep it in `data`; documented at `_billing._consume_budget` and asserted by `e2e_cost_guardrail.py`. Savings baselines skip guard events.
- Blockers: None. Follow-up: `_extract_cost` docstring should point totals at `_spend_cost`.

## 2026-09-26 | Claude Code | PR #791

- Shipped: Reasoning and thinking tokens bill once, inside output. OpenAI and Anthropic output counts already include them, so o-series, gpt-5, and extended-thinking calls were billed high and could trip a dollar budget early. A row with `reasoning_per_1m` reprices only that slice.
- Decisions: No clamp for reasoning > output; both provider SDKs guarantee reasoning ≤ output. `output_usd` in the breakdown is now the non-reasoning part.
- Blockers: None. Gemini `thoughts_token_count` is never read, so Gemini thinking may be under-billed (in `ops/FOLLOWUP.md`).

## 2026-09-26 | Claude Code | PR #793

- Shipped: The LangChain callback prices `on_llm_end` with the same resolver and table as the patched clients. Unknown models were recorded as $0, so a dollar budget never tripped on them; Anthropic cache reads went unbilled. Both fixed.
- Decisions: Under `STRICT_PRECISION`, an unpriceable LangChain call raises `CostResolutionError` after closing its span, as the patched clients do.
- Blockers: None for LangChain. OpenAI and Google price rows still need their pricing pages (network access).

## 2026-09-26 | Claude Code | PR #792

- Shipped: One price table for `estimate_cost` and the patched clients. Claude rows match Anthropic's pricing page (2026-09-26); current Claude models were billed 8x to 137x high and a `gpt-5.5` long prompt at half price. Dated ids price as their base model; unknown Anthropic/OpenAI models price at the provider's top listed rate; total-only usage is never $0.
- Decisions: Google keeps the flat high-water charge until its rows are refreshed. `publish.yml` fails a release when any provider's prices are over 90 days old; PR CI does not check dates.
- Blockers: OpenAI and Google rows (last checked 2026-07-15) need their pricing pages, which the session network blocks; the publish gate fails after 2026-10-13.

## 2026-09-26 | Claude Code | PR #786

- Shipped: `patch_openai` / `patch_openai_async` (and `init()`, `run`) cover the OpenAI Responses API, so the Agents SDK `Runner` stops before its next model call once the budget is spent. Fixed every `AsyncOpenAI`/`AsyncAnthropic` call crashing after `init()`. Raw sync calls with a store reserve (Codex review).
- Decisions: Responses API and Agents SDK are Experimental in the compatibility matrix; the openai floor (1.40.0) predates Responses. `openai-agents` joins the latest compat lock only. Hosted tools, `background=True`, and WebSocket stay unsupported.
- Blockers: None. Reasoning tokens are still billed on top of output tokens; queued separately.

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

2026-10-02 | OpenAI GPT-6 auto | PR review 2026-10-02: merged #807 (82a59fa), complete CI gate and nightly published-wheel verification. Current-head Actions green; local SDK 1380 passed, 3 optional skips, 92.32% coverage; 41 focused and 11 MCP tests passed. Other open PRs remain under review.

2026-10-02 | OpenAI GPT-6 auto | Merged #808 (b6cb0c2), ip-address 10.7.2 lockfile update. Fresh full CI and 11 local MCP tests passed. Existing fast-uri moderate advisory remains in the unchanged dependency tree.

2026-10-02 | OpenAI GPT-6 auto | Merged #789 (3294f45), verified CodeQL upload-sarif 4.38.1 pin. Fresh actionlint, CodeQL and complete CI passed. Paired init/analyze update remains under validation; newly opened #810 addresses the fast-uri advisory.

2026-10-02 | OpenAI GPT-6 auto | Merged #810 (ee14ca4), fast-uri 3.1.8 security patch. Fresh complete CI and 11 local MCP tests passed; npm audit now reports zero vulnerabilities in the MCP dependency tree.

2026-10-02 | OpenAI GPT-6 auto | Merged #788 (6fdd55f), paired CodeQL init/analyze 4.38.2 after reconciling Dependabot updates. Verified upstream tag and fresh actionlint, CodeQL analysis, complete CI. #790 head history is included; final PR state reconciliation pending.

2026-10-02 | OpenAI GPT-6 auto | Verified #790 is MERGED through #788, preserving the reviewed current head in main. Both CodeQL actions now match 4.38.2; actual combined CodeQL analysis passed.

2026-10-02 | OpenAI GPT-6 auto | Merged #806 after fixing dynamic PyPI publish dates, unavailable metadata, list-schema preservation and empty-feed caveats. All 30 activation tests and fresh complete CI passed; review findings resolved. #809 awaits its final updated-head scan/CI.

2026-10-02 | OpenAI GPT-6 auto | Merged #809 (6239a69), pinned advisory scanner with least privilege, telemetry disabled and visible execution errors. Seven wrapper cases, final PR scan and main scan passed. All eight reviewed PRs are merged; final SDK validation: 1392 passed, 3 optional skips, 92.32% coverage. Durable proof: proof/pr-review-20261002/. No review blockers; scanner rule coverage remains limited. No package release performed.

2026-10-02 | OpenAI GPT-6 auto | Merged #811 (ca17961), durable PR-review proof and final handoff. Complete hosted CI and configured local checks passed. No package release or outside adoption claim.

2026-10-02 | OpenAI GPT-6 auto | Merged #812 (2258413), published-version first-use correction and tested Windows PowerShell guide. SDK 1392 passed, 3 optional skips, 92.40% coverage; 40 focused tests and complete current-head CI passed. Review fixes include candidate guide links and redacted proof paths. Outside tester observations remain unknown; #644 still waits on a compatible upstream security fix. All 25 issues remain open.

2026-10-02 | OpenAI GPT-6 auto | Merged #813 (b4d0b61), real Responses instance detection and isolated missing-provider mocks. Two clean installed candidate-wheel profiles passed 13 cases each; full SDK 1396 passed, 3 optional skips, zero warnings, 92.33% coverage; complete CI and independent review passed. Proof: proof/responses-floor-20261002/. Both rows stay Experimental pending automatic floor checks; Chat floor stays 1.40.0. No release or outside-adoption claim.

2026-10-02 | OpenAI GPT-6 auto | Merged #814 (10b3d9a), dated published 1.4.0 Windows/Python 3.11.9 reservation proof: six spawn runs dispatch once/refuse once, zero leftover holds; two in-memory controls still overshoot. Source suite on Python 3.13.2: 1396 passed, 3 optional skips, zero warnings, 92.27% coverage. Complete CI/independent review passed; relative log paths and interpreter labels corrected during review. Proof: proof/windows-reservation-20261002/. No runtime/release/support-promotion change; #736 automation and CrewAI gates remain.

2026-10-02 | OpenAI GPT-6 auto | Merged #815 (1c73ffb), eight real Chat/Anthropic stream/async dispatch cases in existing floor/current CI and updated compatibility/enforcement notes. Two clean installed candidate-wheel profiles passed 8 cases each, zero skips/warnings; source suite on Python 3.13.2: 1404 passed, 3 optional skips, zero warnings, 92.35% coverage. Ubuntu floor/current and full hosted CI passed; Codex found no issues and Claude notes were answered. Proof: proof/real-chat-stream-20261002/. No runtime/API/workflow/release change. Responses/Agents floor automation awaits owner workflow approval; CrewAI #644 and outside-adoption gates remain.

2026-10-02 | OpenAI GPT-6 auto | Merged #819 (980da69), installed candidate-wheel provider floors on Windows/Python 3.9.6: Chat/Anthropic 12 cases and Responses/Agents 13, zero skips/warnings. All 49 installed files and metadata equal the exact wheel; current providers require Python 3.10+. Source suite on Python 3.13.2: 1404 passed, 3 optional skips, zero warnings, 92.33% coverage. PR/main CI, CodeQL and scanner passed; Claude/Copilot cloud found no blocking issue, and Codex missing-ledger finding was fixed and verified in a clean exact-head archive (20/20 artifact checks). Proof: proof/windows-py39-floor-20261002/. #736 remains open for floor automation and CrewAI; workflow proposal still awaits owner authorization.

2026-10-02 | OpenAI GPT-6 auto | Merged #821 (dd24a7b), closes #816: shared resource patching covers standard OpenAI clients created before activation, sync/async Chat and Responses, public init, idempotency and unpatch. Cached-resource-export failure found by floor CI and Copilot was fixed; all final PR/main CI and scans passed. Final source: 1420 passed, 3 optional Agents skips, zero warnings, 92.34% coverage. Installed Windows/Python 3.11 candidate profiles: 20 Chat/Anthropic floor cases and 41 each Responses/Agents floor/current, zero skips/warnings. Exact-head showwork archive: 58/58 artifact checks. Initial Claude/Copilot reviews completed; final automated Claude input was truncated before code and its false log findings were answered with source evidence; supplemental local Claude timed out without a result. Proof: proof/early-openai-clients-816/review-r2/. Saved callables/helpers and custom overrides remain outside coverage; Anthropic activation order and Experimental rows remain. No PyPI release. Next eligible existing-contract bugs: #818 and #820; local pricing configuration #817 needs a reviewed scope decision.

2026-10-02 | OpenAI GPT-6 auto | Merged #822 (f03d0be), closes #818: native Ollama dict/attribute counts now reach manual billing, token budgets and caller-owned JSONL. Prior installed wheel: 15 expected failures/3 passes; fixed Windows/Python 3.9.6 and 3.13.2: 18 cases each, zero skips/warnings, all 49 installed files and metadata equal the wheel. Full SDK: 1438 passed, 3 optional Agents skips, zero warnings, 92.39% coverage. Final PR/main CI and scans passed; Claude, Copilot cloud and Codex completed without blocking findings; quota skips recorded. Clean archive: 31/31 artifact checks; all 22 manifest hashes match repository LF bytes. Proof: proof/ollama-native-usage-818/. Manual accounting and explicit free_local remain; no Ollama interception or PyPI release. Next eligible bug: #820; #817 API exception and Responses-floor workflow proposal await owner decisions.


2026-10-03 | OpenAI GPT-6 auto | Merged #823 (0e96824), closes #820: report, incident and summarize_trace now use earliest valid span start to latest valid span end; the three-call example is 446.6 ms instead of 153 ms. Legacy duration-only fallback and EvalSuite longest-span assertion remain. Copilot found oversized-integer timing crashes; six failing cases were reproduced and fixed. Final focused and installed Windows/Python 3.9.6 and 3.13.2 profiles: 41 cases each, zero skips/warnings; all 49 installed files and metadata equal the wheel. Full SDK: 1479 passed, 3 optional Agents skips, zero warnings, 92.38% coverage. Final PR/main CI and scans passed; complete final diff reviewed by Claude and actual Copilot follow-up, all notes answered, zero unresolved threads. Exact-head archive: 42/42 artifact checks; manifest hashes match repository bytes. Proof: proof/run-duration-820/review-r2/. No PyPI release. No open PRs; 26 issues remain gated. Responses-floor workflow and #817 per-client local-billing API exception await owner decisions; outside-user evidence remains unknown.


2026-10-03 | OpenAI GPT-6 auto | Merged #824 (01ccdcf), #817 documentation slice: removed the promise of accurate local dollar limits through patch_openai; added an existing-API manual free-local example with token/call limits and explicit JSONL. Named Python example is tested and checked against marked Markdown; docs text is not executed. Old guide 1 failed/1 passed; final 2 cases pass on source and verified Windows/Python 3.9.6/3.13.2 candidate and published 1.4.0/Python 3.13.2 installs, zero skips/warnings. Full SDK: 1481 passed, 3 optional Agents skips, zero warnings, 92.38% coverage. Actual report/incident zero cost and optimized-mode refusal verified; final bandit covers the example, zero findings. Final PR and all four triggered main workflows pass. Claude/Copilot source reviews completed, all notes answered; quota skips retained. Exact-head archive: 54/54 artifact checks; 45 manifest entries equal repository blobs. Proof: proof/local-cost-docs-817/review-r3/. SDK runtime/API unchanged; #817 remains open for owner-reviewed per-client configuration. No release; 26 open issues, zero open PRs. Responses-floor workflow and #817 API exception await owner decisions; outside adoption unknown.

2026-10-03 | OpenAI GPT-6 auto | Merged #830 (bb96510), actual Python 3.10 CI-tool lock regeneration with all 21 prior versions/hashes preserved and Windows colorama added. Fresh Python 3.9.6 tools and unchanged SDK candidate install pass; 18 guard tests, full SDK 1584 passed/3 existing optional skips, 92.56% coverage, eight configured checks and final hosted CI pass. Generated graph run 37136759166 selects Python 3.10.20 and receives HTTP 204 for the CI-tool dependency submission on the merge SHA. Independent Copilot final source/proof review clear; Codex proof defects fixed and resolved. Exact-head export verifies 35/35 checks and 28 manifest digests. Proof: proof/graph-runtime-lock-827/. No release or outside-adoption claim.

2026-10-03 | OpenAI GPT-6 auto | Merged #828 (d67c060), Scorecard SARIF uploader 4.38.2, verified annotated tag/commit and unchanged upload inputs/permissions. Copilot and Claude report no blockers; Bugbot explicitly skipped for account mismatch. Branch updated to main and fresh exact-head checks all pass. SDK/API unchanged; actual main upload readback follows in the final review receipt. No release.

2026-10-03 | OpenAI GPT-6 auto | Merged #829 (0376b58), verified Trustabl action 0.4.3 and canonical engine download URL. The action tag matches the pin and includes 0.4.2; engine/rules pins, permissions and telemetry settings stay unchanged. Copilot review clear; all Claude tag concerns answered with live upstream evidence; Bugbot explicitly skipped. Fresh exact-head CI/actionlint/scanner checks pass. SDK/API unchanged. New #831 pytest 9.0.3 security update fails Python 3.9/tool-floor CI and remains held; no unsupported tool pin, SDK-floor change or advisory dismissal was merged.

2026-10-03 | OpenAI GPT-6 auto | Merged #832 (2ea769d), installed Windows candidate-wheel proof for LangChain, LangGraph and OpenTelemetry: three real cases each at minimum versions on Python 3.10.11 and current locked versions on Python 3.13.2, zero skips/errors/failures/warnings. All 51 installed package files and METADATA equal the unchanged candidate wheel; copied Git-blob tests run outside the checkout without repository conftest. The current Ubuntu lock needs a proof-only hash-pinned Windows pywin32 supplement; original failed install retained. Full SDK 1584 passed/3 existing optional skips, 92.56% coverage; eight local checks and all 11 main CI jobs pass (37141568819), plus CodeQL, scanner and Scorecard. Exact archive verifies 42 artifact hashes and showwork 5/5. Bugbot/Copilot quota skips; Claude reviewed the complete final diff and all comments were dispositioned, Codex completed without findings. Owner-admin merge used for the formal approval policy; no failed check bypassed. Proof: proof/windows-frameworks-736/. SDK, CI manifests and support classifications unchanged; 1.4.1 remains unpublished. #736 stays open for CrewAI/#644 and parent gates; #831 remains held for the genuine Python 3.9 pytest security-tool incompatibility.

2026-10-03 | OpenAI GPT-6 auto | Merged #833 (35b6aca), fixes the proof verifier in normal Windows CRLF checkouts. Known UTF-8 text is compared as committed LF; wheel and compressed bytes remain exact. Original checkout failed; post-review LF/CRLF runs pass with distinct input hashes, altered text and wheel both fail. Final ordinary canonical Windows checkout verifies all 53 retained hashes and six installed framework cases. Exact committed export verifies the proof and ledger 6/6; historical mixed-EOL artifact retained unchanged and flaky literal-worker claims replaced with supported direct verification, all error/retraction records preserved. Claude comments fully dispositioned with actual B018 lint proof; Codex completed, Bugbot/Copilot quota skips. Owner-admin merge used for the formal approval policy. All 11 main CI jobs pass (37144389208), CodeQL/scanner/Scorecard pass. No SDK, runtime runner, workflow, dependency, support classification or release changes. Candidate 1.4.1 unpublished; #736 parent/CrewAI gates remain and incompatible pytest #831 stays held.

2026-10-03 (merged 2026-10-04 UTC) | OpenAI GPT-6 auto | Merged #831 (26c4ebc): owner-approved Python3.11 minimum, patched pytest9.0.3, aligned CI/metadata/migration docs and breaking2.0.0 candidate. Actual3.11 compiler preserves19 retained pins/hashes; source1475 pass114 optional-provider skips,91.36% coverage,0 warnings. Installed wheel/offline commands pass, real3.9/3.10 installs reject;12 browser checks and56 committed artifacts/39 source hashes verify. Copilot no blockers; Claude comments answered, Bugbot account skip; owner-admin squash after requiredCI success. All9 mainCI jobs pass (37163554762), Actionlint/CodeQL/scanner/Scorecard pass. PyPI1.4.0 unchanged; no release. Proof: proof/py311-support-831/ and proof/py311-support-closeout-20261004/. New Dependabot #834/#835/#836 now under review; outside-adoption and CrewAI gates remain.

2026-10-04 UTC | OpenAI GPT-6 auto | Merged #834 (2d3fa2c): current OpenAI 3.22.1 locks, fixed Chat 1.40.0 and Responses 1.66.3 floors retained. Four floor files excluded from ordinary Dependabot version updates only; security updates remain enabled. Exact-head full CI and real provider compatibility jobs pass (37165061588). Copilot reviewed and repaired the committed proof checksum; Claude follow-up comments answered, Bugbot account skip. Windows and committed-LF proof verify. No SDK runtime/API or release change. #835 Windows lock repair follows; #837 MCP 2.x is held for real FastMCP/stdio failures and requires a separate migration decision.
