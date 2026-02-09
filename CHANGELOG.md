# Changelog

## 1.0.0
- Production-stable release
- 250+ tests across unit, integration, E2E, performance benchmarks, and DX tests
- Full async test coverage
- Comprehensive guard interaction tests
- All public API exports verified and stable

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
- 48 tests (up from 17), zero lint errors

## 0.2.0
- PyPI-ready packaging with full metadata and publish workflow
- TimeoutGuard: wall-clock time limits for agent runs
- HttpSink: batched HTTP trace ingestion (zero-dependency, stdlib only)
- Real LangChain integration: BaseCallbackHandler with nested span tracking and guard wiring
- CI: Python 3.9–3.12 test matrix + ruff linting
- Blog post: "Why Your AI Agent Loops (And How to See It)"
- Loop failure demo example
- Updated launch posts for HN and LinkedIn/X

## 0.1.0
- Initial SDK: tracing, guards, recorder/replayer, CLI report
- LangChain integration stub
- Demo + E2E test script
- Landing page with Resend capture
