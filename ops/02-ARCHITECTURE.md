# Architecture

## High-level shape

AgentGuard has two product surfaces:

1. A zero-dependency Python SDK that enforces runtime guardrails locally.
2. A hosted dashboard, reached through `HttpSink`, that adds team visibility and control-plane features.

The SDK must stand on its own. It should be usable offline, auditable from source, and credible in production even when the hosted dashboard is not configured.

## Runtime flow

```text
Your agent code
  -> Tracer / instrumentation
  -> Guards evaluate events in-process
  -> Exceptions stop bad behavior immediately
  -> Sinks emit traces

Sinks:
  - JsonlFileSink / StdoutSink for local, offline operation
  - HttpSink for hosted dashboard ingestion
  - OtelTraceSink for OpenTelemetry bridges
```

## Module dependency DAG

Core modules form a DAG with no reverse dependencies:

```text
__init__.py (public API surface)
  -> setup.py -> tracing.py, guards.py, instrument.py, sinks/http.py
  -> tracing.py
  -> guards.py
  -> instrument.py -> guards.py, cost.py
  -> atracing.py -> tracing.py
  -> cost.py
  -> evaluation.py
  -> export.py -> evaluation.py
  -> reporting.py -> evaluation.py
  -> demo.py -> guards.py, tracing.py
  -> doctor.py -> evaluation.py, setup.py
  -> quickstart.py
  -> cli.py -> evaluation.py, reporting.py, demo.py, doctor.py, quickstart.py
  -> sinks/http.py -> tracing.py

Integrations (import core, never the reverse):
  integrations/langchain.py -> guards.py, tracing.py
  integrations/langgraph.py -> guards.py, tracing.py
  integrations/crewai.py -> guards.py, tracing.py
  sinks/otel.py -> tracing.py
```

## Public API surface

42 exports from `sdk/agentguard/__init__.py`:

| Group | Exports |
|-------|---------|
| Tracing | `Tracer`, `TraceSink`, `JsonlFileSink`, `StdoutSink`, `HttpSink`, `summarize_trace` |
| Guards | `BaseGuard`, `LoopGuard`, `FuzzyLoopGuard`, `BudgetGuard`, `TimeoutGuard`, `RateLimitGuard`, `RetryGuard` |
| Exceptions | `AgentGuardError`, `LoopDetected`, `BudgetExceeded`, `BudgetWarning`, `TimeoutExceeded`, `RetryLimitExceeded` |
| Instrumentation | `trace_agent`, `trace_tool`, `patch_openai`, `patch_anthropic`, `unpatch_openai`, `unpatch_anthropic` |
| Async | `AsyncTracer`, `AsyncTraceContext`, `async_trace_agent`, `async_trace_tool`, `patch_openai_async`, `patch_anthropic_async`, `unpatch_openai_async`, `unpatch_anthropic_async` |
| Cost | `estimate_cost` |
| Evaluation | `EvalSuite`, `EvalResult`, `AssertionResult` |
| Setup | `init`, `get_tracer`, `get_budget_guard`, `shutdown` |
| Meta | `__version__` |

Integration modules remain separate imports:

| Module | Exports |
|--------|---------|
| `integrations.langchain` | `AgentGuardCallbackHandler` |
| `integrations.langgraph` | `guarded_node`, `guard_node` |
| `integrations.crewai` | `AgentGuardCrewHandler` |
| `sinks.otel` | `OtelTraceSink` |

## SDK support modules

These modules improve the local SDK experience without blurring the hosted control-plane boundary:

| Module | Purpose |
|--------|---------|
| `reporting.py` | Renders local incident summaries from trace files via `agentguard incident` |
| `demo.py` | Runs a deterministic offline proof of budget, loop, and retry enforcement via `agentguard demo` |
| `doctor.py` | Verifies the local SDK install path and prints the minimal local-only onboarding snippet via `agentguard doctor` |
| `quickstart.py` | Prints framework-specific starter snippets for raw, OpenAI, Anthropic, LangChain, LangGraph, and CrewAI via `agentguard quickstart` |

## Test layout

The SDK test suite is intentionally layered:

- Unit and behavior tests cover guards, tracing, instrumentation, evaluation, export, reporting, and the offline demo.
- Structural tests in `test_architecture.py` enforce the Golden Principles and import graph invariants.
- Integration-style tests use the local ingest server in `tests/conftest.py` instead of depending on a hosted dashboard.
- Production-shaped smoke and DX coverage live in `test_production.py`, `test_dx.py`, and the `e2e_*` files.

Pytest is configured with strict marker and strict config enforcement so stale test configuration fails fast instead of warning.

## Thread safety

All stateful guards and file sinks use `threading.Lock()` on mutable state. This is enforced by `test_architecture.py` through `THREAD_SAFE_CLASSES`.

## Extension points

- Custom guard: subclass `BaseGuard`, implement `check()` and `auto_check()`.
- Custom sink: subclass `TraceSink`, implement `emit(event: Dict[str, Any]) -> None`.
- Custom integration: import core modules and wire them to framework callbacks.

Full architectural rules live in [`GOLDEN_PRINCIPLES.md`](../GOLDEN_PRINCIPLES.md).
