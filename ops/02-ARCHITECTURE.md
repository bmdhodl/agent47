# Architecture

**Last reviewed:** 2026-05-02

## High-level shape

This public repo has three shipped surfaces:

1. A zero-dependency Python SDK that enforces runtime guardrails locally.
2. A read-only MCP server that lets agent clients inspect retained AgentGuard data.
3. A static public site under `site/`.

The hosted dashboard is a separate private product surface. The SDK reaches it
only through explicit hosted integration points such as `HttpSink`.

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

Current boundary:

- Local guards are authoritative for stopping agents in-process.
- `HttpSink` mirrors supported trace and decision events to hosted ingest; it
  does not poll or execute remote kill signals.
- Decision traces are ordinary SDK events named `decision.proposed`,
  `decision.edited`, `decision.overridden`, `decision.approved`, and
  `decision.bound`.
- The MCP server is read-only and exposes retained traces, decisions, alerts,
  usage, costs, and budget health from the read API.
- Dashboard code, billing, retained history, alerts, team workflows, and remote
  control management stay outside this public SDK repo.

## Module dependency DAG

Core modules form a DAG with no reverse dependencies:

```text
__init__.py (public API surface)
  -> setup.py -> repo_config.py, profiles.py, tracing.py, guards.py, instrument.py, sinks/http.py
  -> tracing.py
  -> decision.py -> tracing.py
  -> guards.py
  -> instrument.py -> usage.py, guards.py, cost.py
  -> atracing.py -> tracing.py
  -> cost.py
  -> profiles.py
  -> usage.py
  -> evaluation.py
  -> export.py -> evaluation.py
  -> savings.py -> usage.py, cost.py, evaluation.py
  -> reporting.py -> evaluation.py
  -> demo.py -> guards.py, tracing.py
  -> doctor.py -> evaluation.py, repo_config.py, setup.py
  -> quickstart.py
  -> repo_config.py
  -> cli.py -> evaluation.py, reporting.py, demo.py, doctor.py, quickstart.py, savings.py
  -> sinks/http.py -> tracing.py

Integrations (import core, never the reverse):
  integrations/langchain.py -> guards.py, tracing.py
  integrations/langgraph.py -> guards.py, tracing.py
  integrations/crewai.py -> guards.py, tracing.py
  sinks/otel.py -> tracing.py
```

## Public API surface

52 exports from `sdk/agentguard/__init__.py`:

| Group | Exports |
|-------|---------|
| Tracing | `Tracer`, `TraceSink`, `JsonlFileSink`, `StdoutSink`, `HttpSink`, `summarize_trace` |
| Decision tracing | `DecisionTrace`, `decision_flow`, `log_decision_proposed`, `log_decision_edited`, `log_decision_overridden`, `log_decision_approved`, `log_decision_bound`, `is_decision_event`, `extract_decision_payload`, `extract_decision_events` |
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
| `decision.py` | Emits stable `decision.*` lifecycle events and extracts normalized decision payloads back out of raw traces for local CLI and MCP consumers |
| `usage.py` | Standalone provider inference and usage normalization shared by instrumentation, integrations, and reporting |
| `savings.py` | Computes a local exact-vs-estimated savings ledger from traces using normalized usage data |
| `demo.py` | Runs a deterministic offline proof of budget, loop, and retry enforcement via `agentguard demo` |
| `doctor.py` | Verifies the local SDK install path and prints the minimal local-only onboarding snippet via `agentguard doctor` |
| `profiles.py` | Defines built-in local guard profiles such as `coding-agent` without coupling the SDK to hosted policy management |
| `quickstart.py` | Prints framework-specific starter snippets for raw, OpenAI, Anthropic, LangChain, LangGraph, and CrewAI via `agentguard quickstart` |
| `repo_config.py` | Loads the nearest repo-local `.agentguard.json` file so local defaults stay static, auditable, dashboard-free, and friendly to coding agents |

## Local proof surfaces

The SDK uses deterministic local proof before hosted adoption:

- `agentguard doctor` verifies install and local trace writing.
- `agentguard demo` proves budget, loop, and retry enforcement without network calls.
- `agentguard quickstart` and `examples/starters/` provide minimal stack-specific starters.
- `examples/coding_agent_review_loop.py` demonstrates a coding-agent review/refinement loop stopped by `BudgetGuard` and a patch retry storm stopped by `RetryGuard`.
- `agentguard report` and `agentguard incident` turn local traces into readable proof artifacts.

These proof surfaces should stay offline by default and must not require the
hosted dashboard.

## Test layout

The SDK test suite is intentionally layered:

- Unit and behavior tests cover guards, tracing, instrumentation, evaluation, export, reporting, and the offline demo.
- Structural tests in `test_architecture.py` enforce the Golden Principles and import graph invariants.
- Integration-style tests use the local ingest server in `tests/conftest.py` instead of depending on a hosted dashboard.
- Production-shaped smoke and DX coverage live in `test_production.py`, `test_dx.py`, and the `e2e_*` files.
- Example tests run deterministic local examples in temporary directories so onboarding proofs do not rot.
- Hosted ingest contract tests assert dashboard-facing trace shape without requiring dashboard code in this repo.

Pytest is configured with strict marker and strict config enforcement so stale test configuration fails fast instead of warning.

## Thread safety

All stateful guards and file sinks use `threading.Lock()` on mutable state. This is enforced by `test_architecture.py` through `THREAD_SAFE_CLASSES`.

## Extension points

- Custom guard: subclass `BaseGuard`, implement `check()` and `auto_check()`.
- Custom sink: subclass `TraceSink`, implement `emit(event: Dict[str, Any]) -> None`.
- Custom integration: import core modules and wire them to framework callbacks.

Full architectural rules live in [`GOLDEN_PRINCIPLES.md`](../GOLDEN_PRINCIPLES.md).
