# AGENTS.md

## READ THIS FIRST: SDK Memory
Before touching any code, read these tracked SDK-only memory files. They are
the ground truth for this public repository.

- `memory/state.md` — SDK version, packaging state, current focus
- `memory/blockers.md` — what is blocked, deferred, or not worth more cycles
- `memory/decisions.md` — locked SDK product decisions. Do NOT contradict.
- `memory/distribution.md` — positioning, channels, and audience for SDK growth

**Updated regularly. If `memory/` conflicts with older info in this file, `memory/` wins.**

## Cofounder Inbox
Use `inbox/` to communicate concise SDK status to the cofounder agent.

- `inbox/log.md` is the durable handoff file.
- Write one entry after each merged PR.
- Format each entry as: date, agent, what shipped, decisions made, blockers.
- Keep it SDK-only and short.
- Do not dump business-sensitive plans there.

Key constraints:
- SDK stays free, MIT, zero-dependency. This is non-negotiable.
- Do not build paid features in this repo.
- Distribution > features. Get listed on registries before building new guards.
- Focus is runtime enforcement + coding-agent safety.
- Do not store business-sensitive plans or outreach data in this repo.

---

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What This Is

AgentGuard — a zero-dependency runtime guardrails SDK for coding agents and AI agents. The SDK is open source (MIT, zero dependencies).

- **Repo:** github.com/bmdhodl/agent47
- **Dashboard repo:** github.com/bmdhodl/agent47-dashboard (private)
- **Package:** `agentguard47` on PyPI (latest shipped release: v1.2.7)
- **Landing page:** site/index.html (Vercel)

## Agent Contract (MANDATORY)

**Every Codex session in this repo MUST follow these rules. No exceptions.**

1. **Read ops/ docs first.** Before starting any task, read `ops/00-NORTHSTAR.md`, `ops/03-ROADMAP_NOW_NEXT_LATER.md`, and `ops/04-DEFINITION_OF_DONE.md`.
2. **Stop on conflict.** If your task conflicts with NORTHSTAR or ROADMAP, stop and propose a correction — do not proceed.
3. **Restate before coding.** Before writing any code, explicitly restate:
   - **(a) Goal** — what are we achieving?
   - **(b) Scope** — what files/modules are touched?
   - **(c) Non-goals** — what are we NOT doing?
   - **(d) Done criteria** — how do we know it's done? (reference `ops/04-DEFINITION_OF_DONE.md`)
4. **Structured output.** Every task must include: **plan → diff summary → tests → docs updates needed**.
5. **Check staleness.** Run `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md` and `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`. If ROADMAP is >5 days old or ARCHITECTURE is >14 days old, warn the user before starting any task.
6. **PR proof is required.** Every PR must include concrete proof that the change works: command output, targeted runtime evidence, screenshots when applicable, or saved artifacts under a local proof folder.
7. **Always do the post-PR review loop.** After opening a PR: wait for CI, verify the relevant preview/deployment health, wait a few minutes for automated review, inspect the full PR timeline plus review comments/threads, address feedback, rerun checks, and only then call the PR ready.
8. **Use matching built-in skills by default.** When the task matches them, use `playwright` for browser automation and screenshot proof, `playwright-interactive` when persistent browser state helps, `gh-address-comments` for PR review/comment sweeps, and `vercel-deploy` for deployment work. Do not skip these when the task clearly fits.
9. **Write only high-signal inbox updates.** If the cofounder agent should know about a material SDK blocker or milestone, append one concise entry to `inbox/log.md` after the merged PR instead of writing a long narrative.

## Commands

All common commands are available via `make`:

```bash
make check       # lint + full test suite (mirrors CI)
make preflight   # fast local preflight based on changed files
make release-guard # release metadata and doc-version sync checks
make test        # full test suite with coverage
make structural  # architectural invariant tests only
make lint        # ruff check
make fix         # ruff auto-fix
make security    # bandit security lint
make lines       # module line counts (entropy check)
make install     # pip install SDK + dev tools
make clean       # remove build artifacts
```

If `make` is unavailable in the local shell, run the equivalent underlying commands directly and capture their output as proof.

### Running specific tests

```bash
python -m pytest sdk/tests/test_guards.py -v              # single file
python -m pytest sdk/tests/test_guards.py::TestLoopGuard -v  # single class
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
make release-guard
git tag v1.X.0 && git push origin v1.X.0
# publish.yml auto-publishes to PyPI via PYPI_TOKEN
```

## Architecture

**Two products in this repo (dashboard split to private repo `agent47-dashboard`):**

1. **sdk/** — Python SDK (`agentguard47`). Zero stdlib-only dependencies, Python 3.9+. CI uses `pytest` with coverage enforcement (80% minimum). Public API exports from `agentguard/__init__.py`.

2. **mcp-server/** — MCP server (`@agentguard47/mcp-server`). TypeScript, `@modelcontextprotocol/sdk`. Connects AI agents to the read API via stdio transport.

### Golden Principles

See [GOLDEN_PRINCIPLES.md](GOLDEN_PRINCIPLES.md) for the 10 mechanical rules enforced by CI.
Every rule maps to a structural test in `sdk/tests/test_architecture.py`.

### Module Dependency Graph

Core modules form a DAG — no cycles, no reverse dependencies:

```
__init__.py (public API surface)
    ├── setup.py ──→ tracing.py, guards.py, instrument.py, sinks/http.py
    ├── tracing.py (standalone)
    ├── guards.py (standalone)
    ├── instrument.py ──→ usage.py, guards.py, cost.py
    ├── atracing.py ──→ tracing.py
    ├── cost.py (standalone)
    ├── usage.py (standalone)
    ├── evaluation.py (standalone)
    ├── export.py ──→ evaluation.py
    ├── cli.py ──→ evaluation.py
    └── sinks/http.py ──→ tracing.py

Integration modules (allowed to import core, never the reverse):
    integrations/langchain.py ──→ guards.py, tracing.py
    integrations/langgraph.py ──→ guards.py, tracing.py
    integrations/crewai.py ──→ guards.py, tracing.py
    sinks/otel.py ──→ tracing.py
```

### SDK Key Modules

| Module | Purpose |
|--------|---------|
| `tracing.py` | Tracer, TraceSink, TraceContext, JsonlFileSink, StdoutSink |
| `guards.py` | LoopGuard, FuzzyLoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard, RetryGuard + exceptions |
| `instrument.py` | @trace_agent, @trace_tool, patch_openai, patch_anthropic |
| `usage.py` | Provider inference and normalized token-usage helpers shared across runtime/reporting paths |
| `sinks/http.py` | HttpSink (batched, gzip, retry, SSRF protection) |
| `sinks/otel.py` | OtelTraceSink (OpenTelemetry bridge) |
| `integrations/langchain.py` | LangChain BaseCallbackHandler |
| `integrations/langgraph.py` | LangGraph guarded_node, guard_node |
| `integrations/crewai.py` | CrewAI AgentGuardCrewHandler |
| `evaluation.py` | EvalSuite — chainable assertion-based trace analysis |
| `cli.py` | CLI: report, summarize, eval |
| `atracing.py` | AsyncTracer, AsyncTraceContext — async support |
| `cost.py` | estimate_cost — per-model pricing |
| `export.py` | JSON, CSV, JSONL conversion utilities |

## SDK Conventions

- **Zero dependencies.** Stdlib only. Optional extras: `langchain-core`, `langgraph`, `crewai`, `opentelemetry-api`.
- **Trace format:** JSONL — `{service, kind, phase, trace_id, span_id, parent_id, name, ts, duration_ms, data, error, cost_usd}`
- **Guards raise exceptions:** `LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`, `RetryLimitExceeded`
- **TraceSink interface:** All sinks implement `emit(event: Dict)`

## CI/CD

- **ci.yml:** Python 3.9+3.12 on PRs, full 3.9-3.12 matrix on push to main. `pytest` with `--cov-fail-under=80`, ruff lint.
- **publish.yml:** PyPI publish on `v*` tags.

## Key Decisions

- SDK is the acquisition funnel. Must stay free, MIT, zero-dependency.
- HttpSink bridges SDK to hosted dashboard.

## Agent Workflow

This project uses role-based Codex agents. Each agent has a prompt file in `.Codex/agents/`.

| Role | File | Scope |
|------|------|-------|
| **PM** | `.Codex/agents/pm.md` | Triage, prioritize, coordinate, unblock |
| **SDK Dev** | `.Codex/agents/sdk-dev.md` | `component:sdk` — Python SDK code + tests |
| **Dashboard Dev** | `.Codex/agents/dashboard-dev.md` | Dashboard (private repo: `agent47-dashboard`) |
| **Marketing** | `.Codex/agents/marketing.md` | Docs, README, launch materials, outreach |

**To start an agent session:** Open Codex in this repo and say:
```
Read .Codex/agents/sdk-dev.md and follow those instructions.
```

**Project board:** https://github.com/users/bmdhodl/projects/4

**Current:** latest shipped SDK release is v1.2.7. Read `memory/` for the
current SDK state, blockers, decisions, and distribution priorities.

## Agent Navigation Guide

Step-by-step instructions for common tasks. Follow these patterns for consistency.

### Adding a New Guard

1. Create class in `guards.py` inheriting `BaseGuard`
2. Implement `check()` — must raise an exception (LoopDetected, BudgetExceeded, etc.), never return bool
3. Implement `auto_check(event_name, event_data)` for Tracer integration
4. Add `self._lock = threading.Lock()` if it has mutable state
5. Export from `__init__.py` and add to `__all__`
6. Add to `THREAD_SAFE_CLASSES` in `test_architecture.py` if thread-safe
7. Run `make check`

### Adding a New Sink

1. Create class in `sinks/` inheriting `TraceSink`
2. Implement `emit(event: Dict[str, Any]) -> None`
3. If it uses optional deps, guard with `try/except ImportError`
4. Export from `sinks/__init__.py` and `agentguard/__init__.py`
5. Run `make check`

### Adding a New Integration

1. Create module in `integrations/`
2. Guard third-party imports with `try/except ImportError`
3. Import core modules freely, never the reverse
4. Add optional dependency to `pyproject.toml` `[project.optional-dependencies]`
5. Run `make check`

## What NOT To Do

- Do not add hard dependencies to the SDK.
- Do not use absolute paths in code or scripts.
- Do not commit .env files or secrets.
- Do not create outreach content without verifying the repo is public and package is installable.

## For AI Agents

### Identity

- **Package:** `agentguard47`
- **Version:** latest shipped release is 1.2.7. Check `sdk/pyproject.toml` for the branch version under preparation.
- **Repo:** https://github.com/bmdhodl/agent47
- **License:** MIT
- **Dashboard:** Private repo `agent47-dashboard` (BSL 1.1)

### Project Structure

```
sdk/                          Python SDK source (PyPI: agentguard47)
  agentguard/
    __init__.py               Public API surface -- all exports here
    guards.py                 BudgetGuard, LoopGuard, FuzzyLoopGuard, TimeoutGuard, RateLimitGuard, RetryGuard
    tracing.py                Tracer, TraceContext, TraceSink, JsonlFileSink, StdoutSink
    atracing.py               AsyncTracer, AsyncTraceContext
    instrument.py             @trace_agent, @trace_tool, patch_openai, patch_anthropic
    cost.py                   estimate_cost() -- per-model pricing lookup
    evaluation.py             EvalSuite -- chainable assertion-based trace analysis
    export.py                 JSON, CSV, JSONL conversion
    cli.py                    CLI entrypoint (doctor, demo, report, eval, incident, quickstart)
    usage.py                  Provider inference and normalized token-usage helpers
    sinks/
      http.py                 HttpSink (batched, gzip, retry, SSRF protection)
      otel.py                 OtelTraceSink (OpenTelemetry bridge)
    integrations/
      langchain.py            AgentGuardCallbackHandler
      langgraph.py            guarded_node, guard_node
      crewai.py               AgentGuardCrewHandler
  tests/                      pytest suite, 93% coverage, 80% enforced in CI
  pyproject.toml              Package metadata and version
mcp-server/                   Read-only MCP server (TypeScript, @agentguard47/mcp-server)
docs/                         Guides, cookbooks, competitive analysis
examples/                     Runnable examples and starter files
site/                         Landing page (Vercel)
ops/                          North star, architecture, roadmap, definition of done
memory/                       SDK state, blockers, decisions, distribution priorities
```

### Public API Surface

**Tracing:** `Tracer`, `TraceContext`, `TraceSink`, `JsonlFileSink`, `StdoutSink`, `HttpSink`
**Guards:** `LoopGuard`, `FuzzyLoopGuard`, `BudgetGuard`, `TimeoutGuard`, `RateLimitGuard`, `RetryGuard`
**Exceptions:** `LoopDetected`, `BudgetExceeded`, `BudgetWarning`, `TimeoutExceeded`, `RetryLimitExceeded`
**Instrumentation:** `trace_agent`, `trace_tool`, `patch_openai`, `patch_anthropic`, `unpatch_openai`, `unpatch_anthropic`
**Async:** `AsyncTracer`, `AsyncTraceContext`, `async_trace_agent`, `async_trace_tool`, `patch_openai_async`, `patch_anthropic_async`, `unpatch_openai_async`, `unpatch_anthropic_async`
**Cost:** `estimate_cost`
**Evaluation:** `EvalSuite`, `EvalResult`, `AssertionResult`
**Integrations:** `AgentGuardCallbackHandler` (LangChain), `guarded_node`/`guard_node` (LangGraph), `AgentGuardCrewHandler` (CrewAI), `OtelTraceSink` (OpenTelemetry)

### Guard Parameters

Signatures match `sdk/agentguard/guards.py`. BudgetGuard requires at least one of `max_tokens`, `max_calls`, or `max_cost_usd`; passing none raises `ValueError`.

| Guard | Parameter | Type | Default | Effect |
|-------|-----------|------|---------|--------|
| BudgetGuard | `max_tokens` | Optional[int] | None | Hard stop at this token count |
| BudgetGuard | `max_calls` | Optional[int] | None | Hard stop at this call count |
| BudgetGuard | `max_cost_usd` | Optional[float] | None | Hard stop at this dollar amount |
| BudgetGuard | `warn_at_pct` | Optional[float] | None | Fire warning callback at this percentage (0.0-1.0) |
| BudgetGuard | `on_warning` | Optional[Callable[[str], None]] | None | Called when warn threshold crossed |
| LoopGuard | `max_repeats` | int | 3 | Kill after N identical consecutive tool calls |
| LoopGuard | `window` | int | 6 | History window size for repeat detection |
| FuzzyLoopGuard | `max_tool_repeats` | int | 5 | Kill after N similar tool calls |
| FuzzyLoopGuard | `max_alternations` | int | 3 | Kill after N A-B-A-B pattern alternations |
| FuzzyLoopGuard | `window` | int | 10 | History window size |
| TimeoutGuard | `max_seconds` | float | required | Wall-clock timeout in seconds |
| RateLimitGuard | `max_calls_per_minute` | int | required | Calls-per-minute throttle |
| RetryGuard | `max_retries` | int | 3 | Kill after N retries on the same tool |

### Test Sandbox

Run the full test suite locally:

```bash
pip install -e ./sdk
python -m pytest sdk/tests/ -x --tb=short -q      # fast check
make check                                          # lint + full suite (mirrors CI)
```

Run a local demo (no API keys, no network):

```bash
pip install agentguard47
agentguard doctor       # verify install
agentguard demo         # local proof run
```

### Rate Limits and Constraints

- **Zero dependencies.** Stdlib only. No network calls unless you opt into HttpSink.
- **No API keys required** for local-only mode.
- **CI coverage floor:** 80%. Current: 93%.
- **Guards raise exceptions** (not return codes). Catch `BudgetExceeded`, `LoopDetected`, `TimeoutExceeded`, `RetryLimitExceeded`.
- **TraceSink interface:** All sinks implement `emit(event: Dict)`.
- **Trace format:** JSONL -- `{service, kind, phase, trace_id, span_id, parent_id, name, ts, duration_ms, data, error, cost_usd}`

### Coding Patterns

**Pattern 1: Add a guard to an existing agent**

```python
from agentguard import Tracer, BudgetGuard, patch_openai

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)])
patch_openai(tracer)
# All OpenAI calls are now tracked and budget-enforced
```

**Pattern 2: Stack multiple guards**

```python
from agentguard import Tracer, BudgetGuard, LoopGuard, TimeoutGuard

tracer = Tracer(guards=[
    BudgetGuard(max_cost_usd=10.00),
    LoopGuard(max_repeats=3),
    TimeoutGuard(max_seconds=300),
])
```

**Pattern 3: Trace with structured spans**

```python
with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "search docs"})
    with span.span("tool.search", data={"query": "quantum"}):
        pass  # tool logic
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
```

**Pattern 4: CI cost gate**

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_budget_under(tokens=50_000)
    .assert_no_errors()
    .run()
)
assert result.passed
```

### Key Links

- **PyPI:** https://pypi.org/project/agentguard47/
- **GitHub:** https://github.com/bmdhodl/agent47
- **Docs:** https://github.com/bmdhodl/agent47/tree/main/docs
- **MCP server:** `npx -y @agentguard47/mcp-server`
- **Project board:** https://github.com/users/bmdhodl/projects/4
