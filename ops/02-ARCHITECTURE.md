# Architecture

## High-level diagram

```
┌─────────────────────────────────────────────────┐
│                  Your Agent Code                 │
│  (LangChain / CrewAI / OpenAI / custom)          │
└──────────────┬──────────────────────────────────┘
               │
     ┌─────────▼─────────┐
     │   AgentGuard SDK   │
     │                    │
     │  ┌──────────────┐  │
     │  │   Tracer      │  │  ← spans, events, cost tracking
     │  └──────┬───────┘  │
     │         │          │
     │  ┌──────▼───────┐  │
     │  │   Guards      │  │  ← LoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard
     │  │  (auto_check) │  │    raise exceptions on violations
     │  └──────────────┘  │
     │         │          │
     │  ┌──────▼───────┐  │
     │  │    Sinks      │  │  ← where traces go
     │  │  File│HTTP│OTel│  │
     │  └──────────────┘  │
     └────────────────────┘
               │
    ┌──────────┼──────────────┐
    ▼          ▼              ▼
 .jsonl    Dashboard      Grafana/
 files     (HttpSink)     Datadog
                          (OtelSink)
```

## Module dependency DAG

Core modules form a DAG — no cycles, no reverse dependencies:

```
__init__.py (public API surface)
    ├── setup.py ──→ tracing.py, guards.py, instrument.py, sinks/http.py
    ├── tracing.py (standalone)
    ├── guards.py (standalone)
    ├── instrument.py ──→ guards.py, cost.py
    ├── atracing.py ──→ tracing.py
    ├── cost.py (standalone)
    ├── evaluation.py (standalone)
    ├── export.py ──→ evaluation.py
    ├── cli.py ──→ evaluation.py
    └── sinks/http.py ──→ tracing.py

Integrations (import core, never the reverse):
    integrations/langchain.py ──→ guards.py, tracing.py
    integrations/langgraph.py ──→ guards.py, tracing.py
    integrations/crewai.py ──→ guards.py, tracing.py
    sinks/otel.py ──→ tracing.py
```

## Public API surface

41 exports from `sdk/agentguard/__init__.py`:

| Group | Exports |
|-------|---------|
| Tracing | `Tracer`, `TraceSink`, `JsonlFileSink`, `StdoutSink`, `HttpSink`, `summarize_trace` |
| Guards | `BaseGuard`, `LoopGuard`, `FuzzyLoopGuard`, `BudgetGuard`, `TimeoutGuard`, `RateLimitGuard` |
| Exceptions | `AgentGuardError`, `LoopDetected`, `BudgetExceeded`, `BudgetWarning`, `TimeoutExceeded` |
| Instrumentation | `trace_agent`, `trace_tool`, `patch_openai`, `patch_anthropic`, `unpatch_openai`, `unpatch_anthropic` |
| Async | `AsyncTracer`, `AsyncTraceContext`, `async_trace_agent`, `async_trace_tool`, `patch_openai_async`, `patch_anthropic_async`, `unpatch_openai_async`, `unpatch_anthropic_async` |
| Cost | `estimate_cost` |
| Evaluation | `EvalSuite`, `EvalResult`, `AssertionResult` |
| Setup | `init`, `get_tracer`, `get_budget_guard`, `shutdown` |
| Meta | `__version__` |

Integration modules (separate imports):

| Module | Exports |
|--------|---------|
| `integrations.langchain` | `AgentGuardCallbackHandler` |
| `integrations.langgraph` | `guarded_node`, `guard_node` |
| `integrations.crewai` | `AgentGuardCrewHandler` |
| `sinks.otel` | `OtelTraceSink` |

## Thread safety

All guards and file sinks use `threading.Lock()` on mutable state. Enforced by `test_architecture.py` (`THREAD_SAFE_CLASSES`).

## Extension points

- **Custom guard:** Subclass `BaseGuard`, implement `check()` + `auto_check()`.
- **Custom sink:** Subclass `TraceSink`, implement `emit(event: Dict)`.
- **Custom integration:** Import core modules, wire to framework callbacks.

Full architectural rules: see [`GOLDEN_PRINCIPLES.md`](../GOLDEN_PRINCIPLES.md) (10 rules, all CI-enforced).
