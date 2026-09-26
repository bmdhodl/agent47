# Changelog

## 1.4.1

### Added
- `agentguard receipt <trace.jsonl>` prints each guard stop, the recorded
  cost, and the trace's SHA-256 as a barcode. `--format markdown` wraps it for
  PRs and issues; `--format json` is for CI. Guard events no longer count
  toward the receipt's cost, so the call that tripped a budget is counted once.

- `agentguard hook claude-code` is a Claude Code hook. It refuses the third
  identical tool call in a row, a call that already failed twice, and, with
  `--max-calls`, calls past a per-session cap. `--install --write` adds it to
  `.claude/settings.local.json` and keeps existing hooks; `--uninstall` removes
  only its own. Refusals are logged for `agentguard receipt`. See
  [the guide](docs/guides/claude-code-hook.md).

- `agentguard run [--budget-usd N] agent.py` runs an unmodified script with the
  OpenAI and Anthropic clients patched. Flags, environment variables, and
  `.agentguard.json` set the limits. A guard stop exits 1. Every run ends by
  printing the trace path to stderr for `agentguard receipt`.

### Fixes
- `agentguard --version` prints the installed version and exits 0. In 1.4.0
  it exited 2, often on the first command after install.
- `agentguard report`, `summarize_trace`, `incident`, and
  `EvalSuite.assert_cost_under` no longer count the call that tripped a
  budget twice. `guard.budget_exceeded` echoes that call's cost, which its
  `llm.result` already carries. Savings baselines skip guard events too.

### Docs
- The PyPI README again states that the optional `[crewai]` extra pulls
  ChromaDB with unresolved advisories, including PYSEC-2026-311 /
  CVE-2026-45829. Base installs do not include ChromaDB.
- CONTRIBUTING shows how to add a provider usage fixture in one session.

### Release checks
- Every stable publish now runs the exact PyPI wheel offline on Windows,
  macOS, and Linux. No SDK runtime behavior changed.
- New [compatibility matrix](docs/compatibility.md). CI now runs the full
  suite against the real OpenAI, Anthropic, LangChain, LangGraph, and
  OpenTelemetry packages at the oldest supported versions and at current
  releases. Missing packages fail the job instead of skipping. CrewAI stays
  experimental (#644); the OpenAI Responses API stays unsupported (AG-06).

## 1.4.0

### Stream reservation (AG-05)
- Store-backed OpenAI and Anthropic streams reserve one call before send.
  Final usage commits once. A dropped connection, a provider timeout, or a
  stream that stops early keeps the hold, including after a partial usage
  chunk. Missing usage under a token or dollar cap stays unresolved
  instead of an authoritative zero. A calls-only cap settles one call.
- Unknown model cost is an overestimate. Dated model ids use the owned alias
  map. Cache and reasoning tokens follow the owned price table. Pass
  `prices=` to `resolve_billable_cost` to override that table. No new public
  export.
- In-memory streams, async non-stream calls, and Anthropic non-stream calls
  stay on recorded-budget preflight. Not an invoice cap.

### One local reservation path (AG-04)
- Sync, non-streaming OpenAI Chat Completions now reserve before send when
  `BudgetGuard` has a `StateStore`. One shared key and one remaining call
  produce one dispatch. Commit records provider usage. Cancel frees the hold
  only if the request never left. Timeout, crash, and unknown outcomes keep
  the hold.
- `BudgetGuard.reservation_totals()` reports settled, reserved, and
  unresolved amounts. `check()` and `consume()` are unchanged.
  This slice left streaming, async, and Anthropic on recorded-budget
  preflight. Store-backed streams are the AG-05 note above.
- This is not an invoice cap. Token and dollar holds need `max_tokens` on
  the request. The dollar bound is the owned high-water estimate.

### Local reservation contract (AG-03)
- Designed reserve / commit / cancel / unresolved semantics for a future
  local `StateStore` path:
  [docs/guides/reservation-contract.md](docs/guides/reservation-contract.md).
- Executable private model: `sdk/agentguard/_reservation_contract.py`.
  Unknown provider outcomes cannot silently free funds. No public type.
  `BudgetGuard.check()` still does not reserve. AG-04 wires one OpenAI path.

### Activation evidence (AG-02)
- Landing-page navigation never counts as install or activation.
- `agentguard demo --feedback` prints a local redacted report (`version`,
  `adapter`, `result`, `reproduction`). Users inspect, `--omit`, or decline.
  The demo still makes no network call.
- Weekly classifier: `python scripts/activation_weekly_report.py
  docs/guides/activation-baseline-2026-09-18.json`.
- bmdpat `install_intent` follow-up:
  [docs/guides/bmdpat-measurement-contract.md](docs/guides/bmdpat-measurement-contract.md).

### Honest enforcement boundary (AG-01)
- Published the tested surface map in
  [docs/enforcement-boundary.md](docs/enforcement-boundary.md): advisory,
  recorded-budget preflight, recorded-event preflight, reservation-backed,
  or unsupported.
- Replaced absolute bill-prevention copy with recorded-budget bounds.
  Direct SDK bypass, in-flight spend, missing usage, concurrent overshoot,
  and provider subscription quotas stay documented as remaining exposure.
- Offline reproductions:
  `examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py` and
  `examples/enforcement_boundary/two_worker_overshoot.py`.

## 1.3.2 (2026-09-17)

### Record final usage on streamed provider calls
- OpenAI and Anthropic patches now wrap `stream=True` responses and bill the
  final usage payload once, for both sync and async clients. Anthropic
  `messages.stream()` is included. Chunks without usage are ignored.
- OpenAI streaming requests set `stream_options.include_usage=True` when the
  caller did not set `include_usage`. An explicit `False` is left unchanged.
- Anthropic `create(stream=True)` events split input usage on `message_start`
  and output usage on `message_delta`; the wrapper now merges those fields
  before billing. Stream wrappers are iterators (`next` / `anext`). A failed
  stream closes the trace span with the exception so `assert_no_errors()`
  sees it.
- A stream that ends without usage still counts as one dispatched call with
  zero tokens and zero cost. Exhausted budgets still refuse the request before
  dispatch.
- This does not reserve concurrent capacity, predict a response's cost, or
  preflight goal-level caps. Mid-stream abort without a usage payload cannot
  recover tokens from partial text.
- Reproduce the before/after token counts without network calls with
  `examples/streaming_usage_demo.py`. The provider is mocked; the installed
  AgentGuard patch, stream wrapper, and budget consume path are real.

## 1.3.1 (2026-09-14)

### Stop exhausted-budget retries before provider dispatch
- OpenAI and Anthropic patches now check their supplied budget before calling
  the provider, for both sync and async clients. Catching `BudgetExceeded`
  cannot send another request after the recorded budget reaches its cap.
- Added `BudgetGuard.check()`: a non-consuming check of call, token, and cost
  limits, including zero caps and the current persisted daily budget.
- Successful responses are still charged once. Reset and daily rollover allow
  new calls. Corrupt persisted counters fail closed.
- This is a preflight check, not a concurrent reservation or an estimate of
  the next response. In-flight calls can exceed token/cost caps. Streaming
  usage accounting remains outside this release.
- Reproduce the before/after behavior without network calls with
  `examples/budget_preflight_demo.py`. The provider is mocked; the installed
  AgentGuard patch, guard, and retry loop are real.

## 1.3.0 (2026-09-12)

This release includes the accumulated, unpublished 1.2.14 candidate work below.

### Security and enforcement fixes
- LangChain now propagates guard exceptions through its real callback manager.
  A zero-call budget stops the tool before its body runs; previously LangChain
  could log the exception and continue. Sync and async dispatch run inline.
- Budget and timeout caps reject invalid, negative, boolean, and non-finite
  values. Corrupt stored budget counters fail closed without rewriting state.
  Warning callbacks run outside budget locks and zero limits do not divide by zero.
- Failed x402 payment callbacks refund only their original budget generation,
  so a reset or day rollover cannot reduce a later period's spending.
- HTTP trace delivery rejects credential-bearing URLs, cross-origin redirects,
  mapped private IPv6 addresses, and private/reserved DNS answers at connection
  time. Connections use the validated address while TLS retains hostname checks.
  This transport deliberately does not use environment proxies.
- Retry-After delays are finite, non-negative, and capped at 30 seconds.
- MCP dependency updates resolve the npm audit findings in the committed lockfile.

### Optional dependency compatibility
- LangChain requires 1.6.3+, LangGraph 1.2.11+ with checkpoint 4.2.0+ and SDK
  0.4.4+, OpenTelemetry 1.44.0+, and CrewAI 1.15.21+.
- LangChain and LangGraph extras require Python 3.10+. The dependency-free base
  package remains compatible with Python 3.9+.
- The optional CrewAI tree still installs ChromaDB with four distinct unresolved
  advisories (CVE-2026-45829, CVE-2026-45830, CVE-2026-45831, CVE-2026-45833).
  No fixed upstream version was available in the audit. Avoid this extra unless
  its exposure has been reviewed. Base installs do not include ChromaDB.
- Audit scope, regression results, dependency resolutions, and limitations:
  [September audit](https://github.com/bmdhodl/agent47/blob/v1.3.0/proof/audit-20260912/README.md).


### Reliability
- Added the file-backed `JsonFileStateStore` integration for
  `BudgetGuard(store=...)`, so configured budget usage can persist across
  processes and scheduled tasks. This is local persistence, not distributed
  coordination or a fairness guarantee.
- Hardened the cross-process state lock (`JsonFileStateStore`, used by
  `BudgetGuard(store=...)`) against two Windows races that crashed concurrent
  processes under contention: an exclusive lock create that fails with
  `PermissionError` instead of `FileExistsError` during a concurrent release
  ("delete pending"), and an `os.replace` that transiently fails with
  access-denied when an antivirus/indexer holds the destination. Both now retry
  safely, so cross-process budget enforcement holds on Windows scheduled tasks.

### Budget Goals
- Added `BudgetGuard.goal(...)` for scoped per-goal caps on tokens, calls, and
  cost, with an optional `warn_at_pct` threshold and `on_warning` callback.
  Goal warnings are emitted once per goal while hard caps still refuse excess
  spend.

### Payment Guardrails
- Added `X402SpendGuard` for local caps on total, per-endpoint, and per-call
  x402/USDC spend. It checks and reserves configured spend before payment and
  rolls the reservation back if the payment callback raises. It does not settle
  x402 payments or add a crypto dependency.

### Cost Accounting
- Added maximum-precision billable-cost resolution with explicit source labels
  for provider-reported values, caller prices, estimates, zero-cost tool/local
  work, and unknown cost. Unknown usage stays conservative or fails in strict
  mode; the result is not a provider invoice.

### Usage Accounting
- Anthropic usage normalization now preserves thinking/reasoning tokens and
  separates them from answer tokens when the provider payload exposes that
  detail, alongside cache-read and cache-write fields.

### Hardening
- Rejected NaN, infinite, and negative budget inputs before state mutation so
  non-finite values cannot bypass a cost ceiling.
- Made LoopGuard argument fingerprinting tolerate non-JSON-serializable tool
  arguments instead of crashing the guard while it checks for repeats.

### Public Docs
- Made the reader-facing surface fully model-agnostic to match the
  already-vendor-neutral code path: the README/PyPI "As a skill" heading now
  leads with Codex alongside Claude Code, and the budget-aware escalation
  example notes the escalate target can be any provider's model, not just
  Claude.

### Onboarding
- Bare `agentguard` now prints a friendly first-run welcome with the 60-second
  local path and the star call to action instead of an argparse help dump.
- Added `python -m agentguard` as an entry point so the CLI works even when the
  `agentguard` script is not on PATH.
- Added `agentguard welcome` and `agentguard badge`. `badge` prints a
  paste-able "Guarded by AgentGuard" README badge (markdown, rST, or HTML) so
  adopters can advertise the SDK and drive new installs.

### Distribution
- Added an opt-in bridge to the hosted AgentGuard page
  (`bmdpat.com/tools/agentguard`) from the README/PyPI page, the `agentguard
  --help` footer, and the first-run welcome. These are static links only: the
  SDK still makes no network calls unless you configure `HttpSink`, and nothing
  in the package phones home. The links carry UTM parameters so the site can
  measure click-through; no identifier is sent from your machine.

## 1.2.13

### Release Operations
- Made post-PyPI GitHub Release creation a separate idempotent job and
  dispatch release announcements explicitly, so the release-content workflow no
  longer depends on `GITHUB_TOKEN` release events.
- Hardened generated GitHub Release notes and release-content announcements so
  they start from the last published GitHub Release instead of a stale raw tag.
  This lets `v1.2.13` supersede the failed `v1.2.11` and `v1.2.12` tags without
  truncating public release notes.
- Includes the release candidate originally prepared under the failed
  `v1.2.11` tag. That tag did not publish to PyPI and has no GitHub Release.
- Supersedes the stale `v1.2.12` tag, which was pushed from a checkout still
  carrying `sdk/pyproject.toml` version `1.2.10`. That tag did not publish a new
  PyPI version and has no GitHub Release.

### Reliability
- Hardened `agentguard.__version__` so malformed local package metadata falls
  back to `0.0.0-dev` instead of crashing source-checkout imports.
- Fixed the coding-agent review-loop proof to record cumulative guard spend as
  `total_cost_usd`, preventing local reports from double-counting the stopped
  budget event.

### Public Docs
- Corrected the README threat-model copy so AgentGuard is positioned as local
  runtime hard stops for loops, retries, and budget burn, not as a replacement
  for egress firewalls or tool-permission layers.
- Added release runbook documentation for tag-triggered PyPI publish and
  GitHub Release creation.

### Profiles
- Added a `deployed-agent` guard profile (`agentguard.init(profile="deployed-agent")`)
  for unattended production agents. Tightens defaults to `loop_max=2`,
  `retry_max=1`, `warn_pct=0.5`. Motivated by the arxiv:2605.00055
  ambient-persuasion incident where a deployed agent installed 107
  unauthorized components and overrode its own oversight gate.

### Release Proof
- Added a deterministic sticky agent proof example that simulates a
  CrewAI-style retry storm, repeated tool loop, budget burn, local incident
  output, and dashboard-compatible hosted NDJSON without adding dependencies.
- Added contract tests that post the sticky proof NDJSON to the local hosted
  ingest harness so SDK proof events stay aligned with dashboard expectations.

### Activation
- Added `python -m agentguard.cli ...` fallback guidance to `doctor`, `demo`,
  and `quickstart` so first-run users are not blocked when console scripts
  install outside `PATH`.
- Added a post-demo next-step block so `agentguard demo` points directly to
  `agentguard quickstart --framework raw --write`, the generated starter, and
  the follow-up local report command.
- Added an MCP read-path proof to the proof gallery and test coverage that
  catches stale local example and sample-doc references.
- Added an optional local-first Pydantic AI starter recipe using Pydantic AI's
  `TestModel`, so users can try the pattern without API keys or network calls
  after installing the optional framework package.
- Clarified incident-report dashboard handoff copy so hosted ingest is framed as
  useful when incidents need retained history, alerts, spend trends, or
  team-visible follow-up, not as a requirement for local safety.
- Added a concise local-vs-hosted adoption table to the README and dashboard
  contract docs so the dashboard CTA is explicit without making local SDK use
  feel limited.

### Release Security
- Switched the PyPI publish workflow from long-lived `PYPI_TOKEN` authentication
  to OIDC Trusted Publishing for the `pypi` GitHub environment, with PyPI
  attestations enabled for release artifacts.
- Added release documentation for the required PyPI trusted-publisher tuple and
  post-release verification steps.
- Added an MCP package publishing checklist and normalized npm package metadata
  so the `@agentguard47/mcp-server` release path does not rely on npm publish
  autocorrections.
- Added an optional release-guard npm check so release operators can verify the
  repo MCP package version is actually published as npm latest without making
  normal CI depend on the network.

### Release Operations
- Added a release cadence document that separates the weekly MCP / Glama
  distribution train from the monthly SDK release train.
- Added a scheduled release cadence workflow that opens or updates one active
  release queue issue with SDK, npm MCP, and Glama indexing status.
- Added tag/version validation to the PyPI publish workflow and creates the
  GitHub Release only after PyPI publish succeeds.
- Changed release announcement automation to run from a published GitHub Release
  instead of a raw tag push, so failed PyPI publishes cannot announce as shipped.
- Refreshed the MCP server lockfile so `npm audit` no longer reports the
  transitive `fast-uri` or `qs` advisories.

## 1.2.10

### Activation Proof Path
- Tightened the README and getting-started path around `doctor`, `demo`, and `quickstart` so first-time SDK users can reach local guard proof faster.
- Added a coding-agent review-loop proof artifact that shows budget and retry guards stopping a simulated review/refinement loop without API keys or network calls.
- Added sync coverage for the public sample incident and generated PyPI README so release-facing activation assets do not silently drift.

### Release And Distribution Hygiene
- Added an opt-in activation metrics design doc that defines allowed activation questions and local-first consent boundaries without adding telemetry.
- Hardened release discussion category handling so missing GitHub Discussion categories do not block the package release path.
- Updated the package build timestamp seed to the ZIP-safe reproducible epoch so local and CI release builds do not fail on pre-1980 metadata.
- Clarified hosted ingest language in incident reporting so `HttpSink` is described as event mirroring for retained alerts and follow-up, not a remote kill switch by itself.

## 1.2.9

### Dashboard Contract Alignment
- Decision-trace helpers now emit non-empty dashboard-parseable `binding_state` values for proposed, edited, overridden, and approved events by default.
- Added hosted-ingest contract coverage for decision-trace warnings so SDK events stay queryable by the dashboard after ingest.
- Tightened README and guide copy around the local runtime-control proof path, hosted dashboard handoff, and remote-kill polling boundary.

## 1.2.8

### Agent Security Stack Positioning
- Added a new competitive-positioning doc that places AgentGuard in the runtime behavior and budget layer of the emerging agent security stack, beside identity, MCP governance, and sandboxing layers.
- Updated the README competitive-doc links so the public repo points to both the gateway comparison and the broader stack-layer framing.

### Per-Token Budget Proof
- Added a new local `examples/per_token_budget_spike.py` proof that prices turns from token counts and shows `BudgetGuard` catching a single oversized turn without any API key or network access.
- Updated README, getting-started docs, and examples docs to frame budget enforcement around token-metered pricing and point users to the new local proof path.

### Budget-Aware Escalation Guard
- Added `BudgetAwareEscalation`, `EscalationSignal`, and `EscalationRequired` so developers can keep a cheaper default model and escalate only hard turns to a stronger model without adding provider-specific SDK dependencies.
- Added support for token-count, confidence, tool-call-depth, and custom-rule escalation triggers, plus a local example and guide for the Llama-to-Claude advisor-style pattern.

### Managed-Agent Session Correlation
- Added optional `session_id` support to `Tracer`, `AsyncTracer`, and `agentguard.init(...)` so disposable harnesses can correlate multiple trace streams under one higher-level managed-agent session without changing sink behavior.
- Added a local managed-session guide plus a runnable example that proves two separate tracer instances can emit distinct `trace_id` values while sharing one `session_id`.

### Coding-Agent Skill Packs
- Added `agentguard skillpack` so developers and coding agents can generate repo-local `.agentguard.json` defaults plus instruction files for Codex, Claude Code, GitHub Copilot, and Cursor without bespoke copy-paste setup.
- Updated the coding-agent onboarding docs to prefer the generated local-first skill-pack flow and the `quickstart --write` verification loop over checked-in example paths.

### Supply Chain And Release Prep
- Replaced unhashed workflow `pip install` steps with a checked-in, hash-locked CI toolchain requirements file and switched CI, entropy, and publish validation to use that shared lock.
- Pinned the root and MCP server Dockerfiles to the current `node:22-alpine` image digest to remove mutable base-image references from the repo's build surfaces.
- Prepared the GitHub side of PyPI Trusted Publishing by adding the `pypi` environment and wiring the publish workflow to it, while deliberately keeping token auth in place until the PyPI project owner adds the matching trusted publisher.

## 1.2.7

### Decision Tracing
- Added a new stdlib-only `decision.py` core module with stable `decision.proposed`, `decision.edited`, `decision.overridden`, `decision.approved`, and `decision.bound` event helpers.
- Added the `DecisionTrace` stateful helper plus `decision_flow(...)` so one approval workflow can emit proposal, human edit, approval, and binding events without custom event plumbing.
- Added a local decision-trace example workflow plus guide-level docs and migration notes; the feature reuses the normal AgentGuard event pipeline and requires no sink changes.
- Added `extract_decision_payload(...)`, `extract_decision_events(...)`, and the local `agentguard decisions` CLI so decision traces are queryable without ad hoc JSON parsing.

### SDK Distribution Copy
- Tightened the public SDK and MCP copy around the coding-agent wedge: local-first runtime guardrails, retry-storm prevention, and read-only MCP access to traces, alerts, costs, usage, and budget health.
- Refreshed the SDK package and MCP package descriptions so PyPI, npm, and MCP registry metadata all repeat the same narrow distribution story.

### Hosted Ingest Gating
- Hardened the local ingest test harness so it now rejects `kind="meta"` payloads and requires the hosted `type` alias, matching the contract that previously caused `HttpSink` batches to 400 in production.
- Added hosted-ingest regression tests that fail if watermark events leak into HTTP batches or if release smoke validation stops proving a trace by exact `trace_id`.
- Added a real SDK test gate to the tag-based publish workflow so PyPI publishes are blocked if the hosted-ingest regression suite, lint, or security checks fail.

### Trace and MCP Hardening
- Reused the core tracer's JSON-sanitization primitives for decision traces so large or messy payloads preserve queryable top-level keys instead of collapsing to opaque markers.
- Added a dedicated `get_trace_decisions` MCP tool plus first-party MCP server tests, and wired the MCP build/test path into CI, `make check`, and SDK preflight.
- Added release-guard coverage for MCP package metadata so `mcp-server/package.json` and `mcp-server/server.json` cannot drift during release prep.

## 1.2.6

### Hosted Ingest Compatibility
- `HttpSink` now drops local-only `kind="meta"` watermark records before posting to the hosted ingest API, preventing first-batch 400s from validators that only accept trace spans and point events.
- `HttpSink` now mirrors supported trace kinds into both `kind` and `type` on outbound payloads so the SDK remains compatible across hosted validators while preserving local SDK semantics.

## 1.2.5

### Distribution and Registry Hygiene
- Added official MCP Registry metadata plus package-local Docker and Smithery config for `@agentguard47/mcp-server`.
- Added `sdk/tests/test_mcp_registry_metadata.py` to keep MCP registry metadata, packaging files, and environment-variable contracts aligned.
- Refreshed README, SDK README, PyPI README, and package metadata around coding-agent safety and local-first onboarding.

### Public Repo Hygiene
- Removed stale tracked `context/` files that carried business-sensitive planning data not meant for the public SDK repo.
- Retired the obsolete `inbox/INBOX_PROTOCOL.md` workflow in favor of the current `memory/` plus `inbox/log.md` contract.

## 1.2.4

### Coding-Agent Onboarding
- Added repo-local `.agentguard.json` support so humans and coding agents can share static SDK defaults without dashboard coupling.
- Added the built-in `coding-agent` profile with tighter loop and retry defaults for repo automation and coding workflows.
- Added executable starter files under `examples/starters/` and aligned `agentguard doctor` / `agentguard quickstart` around `.agentguard/traces.jsonl`.
- Added the `docs/guides/coding-agents.md` onboarding guide plus doc updates across the README, SDK README, examples, architecture doc, roadmap, and generated PyPI README.

### SDK Hardening
- `JsonlFileSink` now creates parent directories automatically so repo-local trace paths like `.agentguard/traces.jsonl` work out of the box.
- Repo-config parsing now rejects boolean values in numeric fields to keep local defaults deterministic and auditable.
- `init()` now still honors repo-level profile defaults when service, budget, or trace path are passed explicitly but guard-profile values are left implicit.
- Invalid `AGENTGUARD_BUDGET_USD` values now fall back to a valid repo-local `budget_usd` instead of silently dropping budget enforcement.

## 1.2.3

### Release Hardening
- Removed the dashboard API key prefix from `examples/cost_guardrail.py` log output.
- Replaced insecure `tempfile.mktemp()` usage in `sdk/tests/e2e_v110.py` with secure named temp files.
- Pinned GitHub Actions by commit SHA across CI, publish, CodeQL, Scorecard, and maintenance workflows.

### Docs and Release Hygiene
- Refreshed stale docs and agent instructions to point at the latest shipped release (`v1.2.2`) instead of `v1.2.1`.
- Replaced dead `agentguard view` references with supported `agentguard report` / `agentguard incident` commands.
- Added explicit release criteria to `ops/04-DEFINITION_OF_DONE.md`.
- Updated the SDK roadmap to reflect the feature freeze and release-hardening focus.

## 1.2.2

### SDK Reliability
- Added `RetryGuard` to stop retry storms with a dedicated `RetryLimitExceeded` exception.
- Refreshed built-in Anthropic and Google pricing entries used by `estimate_cost()`.
- Expanded evaluation assertions and incident reporting for local trace analysis.

### Local Proof and Onboarding
- Added `agentguard demo` for a deterministic offline proof of budget, loop, and retry enforcement.
- Added `agentguard doctor` for local-only install verification and minimal next-step guidance.

## 1.1.0

### Cost Guardrail Pipeline
- **BudgetGuard in auto-patchers:** `patch_openai(tracer, budget_guard=guard)` — every LLM call's cost/tokens automatically fed into the guard. Works with all 4 patchers (OpenAI/Anthropic, sync/async).
- **guard.budget_exceeded event:** Emitted to the trace sink before `BudgetExceeded` is raised, so the event appears in your dashboard even when the agent is killed.
- **guard.budget_warning event:** Emitted when the `warn_at_pct` threshold is crossed during an auto-patched call.
- **cost_usd promoted to top-level:** Auto-patchers now emit `cost_usd` as a top-level event field instead of burying it inside `data`. Dashboard-compatible (uses `ev.cost_usd ?? ev.data.cost_usd`).

### Bug Fixes
- **Cost double-counting fix:** `_extract_cost()` helper prefers top-level `cost_usd`, falls back to `data.cost_usd`, never sums both. Used by `summarize_trace()`, CLI `report`, and `EvalSuite`.
- **sampling_rate validation:** `Tracer(sampling_rate=...)` now rejects values outside [0.0, 1.0].
- **Guards fire when sampled out:** Guards check every event even when `sampling_rate < 1.0` causes trace emission to be skipped.

### Hardening
- **HttpSink max_buffer_size:** Default 10,000 events. Drops oldest events when buffer is full to prevent OOM on unreachable endpoints.
- **AsyncTraceContext.event()** now accepts `cost_usd` parameter (parity with sync `TraceContext`).

### Security (from v1.1.0-rc)
- BaseGuard abstract class with clean `auto_check()` dispatch
- Thread safety: `threading.Lock` on BudgetGuard and RateLimitGuard
- IDN/Punycode SSRF bypass protection in HttpSink URL validation
- Span/event name length limits (1000 chars, logged warning on truncation)
- TimeoutGuard context manager support
- Tracer context manager for clean `sink.shutdown()` on exit

### Testing
- 35 new cost guardrail tests, 19-check e2e verification script
- 422+ tests passing, lint clean

## 1.0.0

- Production-stable GA release
- 317 tests, 86% coverage across unit, integration, and E2E
- Comprehensive README with guards reference, 5 integration guides, architecture diagram
- CONTRIBUTING.md with full dev setup and code style guide
- All public API exports verified and stable

## 0.8.0

- SSRF protection in HttpSink (block private/loopback IPs)
- CI coverage enforcement with `--cov-fail-under=80`
- Coverage artifact upload on Python 3.12 runs
- Input validation hardening across guards and sinks

## 0.7.0

- LangGraph integration: `guarded_node` decorator and `guard_node` wrapper
- CrewAI integration: `AgentGuardCrewHandler` with step and task callbacks
- OpenTelemetry TraceSink: bridge AgentGuard events to OTel spans with parent-child linking
- OTLP-compatible JSON export
- 49 new integration tests

## 0.6.0

- Rebrand to `agentguard47` on PyPI
- Version reset from premature 1.0.0 to 0.6.0 (Beta classifier)
- Clean publish workflow with token auth

## 0.5.0

- Async support: AsyncTracer, AsyncTraceContext, async_trace_agent, async_trace_tool
- Async monkey-patches: patch_openai_async, patch_anthropic_async
- Unpatch helpers: unpatch_openai, unpatch_anthropic (sync + async)
- py.typed marker for PEP 561 type checking support

## 0.4.0

- Cost tracking: CostTracker, estimate_cost, update_prices with per-model pricing (OpenAI, Anthropic, Gemini, Mistral)
- BudgetWarning callback via warn_at_pct parameter
- FuzzyLoopGuard: A-B-A-B alternation detection, same-tool frequency analysis
- RateLimitGuard: calls-per-minute enforcement
- Export module: JSON, CSV, JSONL conversion utilities
- HttpSink hardening: gzip compression, retry with exponential backoff, 429 handling, idempotency keys, sampling, metadata headers

## 0.3.0

- Evaluation as Code: EvalSuite with chainable assertions (no_loops, tool_called, budget_under, completes_within, event_exists, no_errors)
- Auto-instrumentation: @trace_agent and @trace_tool decorators, patch_openai() and patch_anthropic() monkey-patches
- Gantt trace viewer: timeline visualization with color-coded spans, click-to-expand detail panel, aggregate stats
- CLI: `agentguard eval traces.jsonl` runs default assertions with exit code

## 0.2.0

- PyPI-ready packaging with full metadata and publish workflow
- TimeoutGuard: wall-clock time limits for agent runs
- HttpSink: batched HTTP trace ingestion (zero-dependency, stdlib only)
- Real LangChain integration: BaseCallbackHandler with nested span tracking and guard wiring
- CI: Python 3.9-3.12 test matrix + ruff linting

## 0.1.0

- Initial SDK: tracing, guards, recorder/replayer, CLI report
- LangChain integration stub
- Demo + E2E test script
- Landing page with Resend capture
