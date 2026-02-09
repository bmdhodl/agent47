# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AgentGuard — a lightweight observability and runtime-guards SDK for multi-agent AI systems. The SDK is open source (MIT, zero dependencies).

- **Repo:** github.com/bmdhodl/agent47
- **Dashboard repo:** github.com/bmdhodl/agent47-dashboard (private)
- **Package:** `agentguard47` on PyPI (v1.0.0 GA)
- **Landing page:** site/index.html (Vercel)

## Commands

### SDK (Python)

```bash
# Run all tests (from repo root)
python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing

# Run a single test file
python -m pytest sdk/tests/test_guards.py -v

# Run a single test case
python -m pytest sdk/tests/test_guards.py::TestLoopGuard::test_loop_detected -v

# Lint
ruff check sdk/agentguard/

# Install SDK in editable mode
pip install -e ./sdk

# Install dev tools
pip install pytest pytest-cov ruff
```

### MCP Server

```bash
cd mcp-server
npm ci                # Install deps
npm run build         # Compile TypeScript
npm start             # Run (requires AGENTGUARD_API_KEY env var)
```

### Publishing

```bash
# Bump version in sdk/pyproject.toml, then:
git tag v1.X.0 && git push origin v1.X.0
# publish.yml auto-publishes to PyPI via PYPI_TOKEN
```

## Architecture

**Two products in this repo (dashboard split to private repo `agent47-dashboard`):**

1. **sdk/** — Python SDK (`agentguard47`). Zero stdlib-only dependencies, Python 3.9+. CI uses `pytest` with coverage enforcement (80% minimum). Public API exports from `agentguard/__init__.py`.

2. **mcp-server/** — MCP server (`@agentguard47/mcp-server`). TypeScript, `@modelcontextprotocol/sdk`. Connects AI agents to the read API via stdio transport.

### SDK Key Modules

| Module | Purpose |
|--------|---------|
| `tracing.py` | Tracer, TraceSink, TraceContext, JsonlFileSink, StdoutSink |
| `guards.py` | LoopGuard, FuzzyLoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard + exceptions |
| `instrument.py` | @trace_agent, @trace_tool, patch_openai, patch_anthropic |
| `sinks/http.py` | HttpSink (batched, gzip, retry, SSRF protection) |
| `sinks/otel.py` | OtelTraceSink (OpenTelemetry bridge) |
| `integrations/langchain.py` | LangChain BaseCallbackHandler |
| `integrations/langgraph.py` | LangGraph guarded_node, guard_node |
| `integrations/crewai.py` | CrewAI AgentGuardCrewHandler |
| `evaluation.py` | EvalSuite — chainable assertion-based trace analysis |
| `recording.py` | Recorder, Replayer (deterministic replay) |
| `cli.py` | CLI: report, summarize, view, eval |
| `atracing.py` | AsyncTracer, AsyncTraceContext — async support |
| `cost.py` | CostTracker, estimate_cost, update_prices — per-model pricing |
| `export.py` | JSON, CSV, JSONL conversion utilities |

## SDK Conventions

- **Zero dependencies.** Stdlib only. Optional extras: `langchain-core`, `langgraph`, `crewai`, `opentelemetry-api`.
- **Trace format:** JSONL — `{service, kind, phase, trace_id, span_id, parent_id, name, ts, duration_ms, data, error, cost_usd}`
- **Guards raise exceptions:** `LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`, `RateLimitExceeded`
- **TraceSink interface:** All sinks implement `emit(event: Dict)`

## CI/CD

- **ci.yml:** Python 3.9-3.12 matrix, `pytest` with `--cov-fail-under=80`, ruff lint. Runs on push/PR.
- **publish.yml:** PyPI publish on `v*` tags.

## Key Decisions

- SDK is the acquisition funnel. Must stay free, MIT, zero-dependency.
- HttpSink bridges SDK to hosted dashboard.

## Agent Workflow

This project uses role-based Claude Code agents. Each agent has a prompt file in `.claude/agents/`.

| Role | File | Scope |
|------|------|-------|
| **PM** | `.claude/agents/pm.md` | Triage, prioritize, coordinate, unblock |
| **SDK Dev** | `.claude/agents/sdk-dev.md` | `component:sdk` — Python SDK code + tests |
| **Dashboard Dev** | `.claude/agents/dashboard-dev.md` | Dashboard (private repo: `agent47-dashboard`) |
| **Marketing** | `.claude/agents/marketing.md` | Docs, README, launch materials, outreach |

**To start an agent session:** Open Claude Code in this repo and say:
```
Read .claude/agents/sdk-dev.md and follow those instructions.
```

**Project board:** https://github.com/users/bmdhodl/projects/4

**Current:** v1.0.0 GA shipped. See project board for priorities.

## What NOT To Do

- Do not add hard dependencies to the SDK.
- Do not use absolute paths in code or scripts.
- Do not commit .env files or secrets.
- Do not create outreach content without verifying the repo is public and package is installable.

## For AI Agents

### Identity

- **Package:** `agentguard47`
- **Version:** 1.0.0
- **Repo:** https://github.com/bmdhodl/agent47
- **License:** MIT
- **Dashboard:** Private repo `agent47-dashboard` (BSL 1.1)

### Public API Surface

**Tracing:** `Tracer`, `TraceContext`, `TraceSink`, `JsonlFileSink`, `StdoutSink`, `HttpSink`
**Guards:** `LoopGuard`, `FuzzyLoopGuard`, `BudgetGuard`, `TimeoutGuard`, `RateLimitGuard`
**Exceptions:** `LoopDetected`, `BudgetExceeded`, `BudgetWarning`, `TimeoutExceeded`
**Instrumentation:** `trace_agent`, `trace_tool`, `patch_openai`, `patch_anthropic`, `unpatch_openai`, `unpatch_anthropic`
**Async:** `AsyncTracer`, `AsyncTraceContext`, `async_trace_agent`, `async_trace_tool`, `patch_openai_async`, `patch_anthropic_async`, `unpatch_openai_async`, `unpatch_anthropic_async`
**Cost:** `CostTracker`, `estimate_cost`, `update_prices`
**Evaluation:** `EvalSuite`, `EvalResult`, `AssertionResult`
**Recording:** `Recorder`, `Replayer`
**Integrations:** `AgentGuardCallbackHandler` (LangChain), `guarded_node`/`guard_node` (LangGraph), `AgentGuardCrewHandler` (CrewAI), `OtelTraceSink` (OpenTelemetry)

### Constraints

- Zero dependencies (Python stdlib only, Python 3.9+)
- CI uses `pytest` with coverage enforcement (80% min)
- Guards raise exceptions (not return codes)
- All public API exports from `sdk/agentguard/__init__.py`

### Key Links

- **Project board:** https://github.com/users/bmdhodl/projects/4
