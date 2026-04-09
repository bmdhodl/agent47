# Changelog

## Unreleased

### Coding-Agent Skill Packs
- Added `agentguard skillpack` so developers and coding agents can generate repo-local `.agentguard.json` defaults plus instruction files for Codex, Claude Code, GitHub Copilot, and Cursor without bespoke copy-paste setup.
- Updated the coding-agent onboarding docs to prefer the generated local-first skill-pack flow and the `quickstart --write` verification loop over checked-in example paths.

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
