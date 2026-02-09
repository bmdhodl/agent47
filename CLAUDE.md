# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AgentGuard — a lightweight observability and runtime-guards SDK for multi-agent AI systems. The SDK is open source (MIT, zero dependencies).

- **Repo:** github.com/bmdhodl/agent47
- **Dashboard repo:** github.com/bmdhodl/agent47-dashboard (private)
- **Package:** `agentguard47` on PyPI (v0.8.0)
- **Landing page:** site/index.html (Vercel)

## Commands

### SDK (Python)

```bash
# Run all tests (from repo root)
PYTHONPATH=sdk python3 -m unittest discover -s sdk/tests -v

# Run a single test file
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards -v

# Run a single test case
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards.TestLoopGuard.test_loop_detected -v

# Lint
ruff check sdk/agentguard/

# Install SDK in editable mode
pip install -e ./sdk
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
git tag v0.X.0 && git push origin v0.X.0
# publish.yml auto-publishes to PyPI via PYPI_TOKEN
```

## Architecture

**Two products in this repo (dashboard split to private repo `agent47-dashboard`):**

1. **sdk/** — Python SDK (`agentguard47`). Zero stdlib-only dependencies, Python 3.9+. All tests use `unittest` (no pytest). Public API exports from `agentguard/__init__.py`.

2. **mcp-server/** — MCP server (`@agentguard47/mcp-server`). TypeScript, `@modelcontextprotocol/sdk`. Connects AI agents to the read API via stdio transport.

### SDK Key Modules

| Module | Purpose |
|--------|---------|
| `tracing.py` | Tracer, TraceSink, TraceContext, JsonlFileSink, StdoutSink |
| `guards.py` | LoopGuard, BudgetGuard, TimeoutGuard + exceptions |
| `instrument.py` | @trace_agent, @trace_tool, patch_openai, patch_anthropic |
| `sinks/` | HttpSink (batched background thread) — bridge to dashboard |
| `integrations/` | LangChain BaseCallbackHandler |
| `evaluation.py` | EvalSuite — chainable assertion-based trace analysis |
| `recording.py` | Recorder, Replayer (deterministic replay) |
| `cli.py` | CLI: report, summarize, view, eval |
| `atracing.py` | AsyncTracer, AsyncTraceContext — async support |
| `cost.py` | CostTracker, estimate_cost, update_prices — per-model pricing |
| `export.py` | JSON, CSV, JSONL conversion utilities |

## SDK Conventions

- **Zero dependencies.** Stdlib only. Optional extras: `langchain-core>=0.1`.
- **Trace format:** JSONL — `{service, kind, phase, trace_id, span_id, parent_id, name, ts, duration_ms, data, error, cost_usd}`
- **Guards raise exceptions:** `LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`
- **TraceSink interface:** All sinks implement `emit(event: Dict)`

## CI/CD

- **ci.yml:** Python 3.9-3.12 matrix tests + ruff lint. Runs on push/PR.
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

**How agents coordinate:**
- The GitHub project board is the single source of truth.
- Issues are separated by `component:` labels (sdk, dashboard, api, infra).
- Agents pick up Todo items, move to In Progress, do the work, close when done.
- Cross-agent dependencies are handled via issue comments and references.
- When blocked, agents comment on the issue and tag the blocking issue number.
- New work discovered during implementation gets filed as new issues with proper labels.

**Current:** See project board for priorities.

## What NOT To Do

- Do not add hard dependencies to the SDK.
- Do not use absolute paths in code or scripts.
- Do not commit .env files or secrets.
- Do not create outreach content without verifying the repo is public and package is installable.
- Do not mix implementation, testing, deployment, and strategy in one mega-session.

## For AI Agents

Structured context for AI agents working on or with this project.

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

### File Layout

```
agent47/
├── sdk/agentguard/    # Python SDK (PyPI: agentguard47)
├── mcp-server/        # MCP server for AI agent access
├── site/              # Landing page
├── scripts/           # Automation scripts
├── docs/              # Public examples and blog posts
├── .claude/agents/    # Agent role prompts
└── .github/workflows/ # CI, publish, scout
```

### Constraints

- Zero dependencies (Python stdlib only, Python 3.9+)
- All tests use `unittest` (no pytest)
- Guards raise exceptions (not return codes)
- All public API exports from `sdk/agentguard/__init__.py`

### Current State

v1.0.0 shipped. See project board for current priorities.

### Key Links

- **Project board:** https://github.com/users/bmdhodl/projects/4
