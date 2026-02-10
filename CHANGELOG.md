# Changelog

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
