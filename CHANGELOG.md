# Changelog

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
