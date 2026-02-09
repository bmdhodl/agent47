# Changelog

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
