# AgentGuard

[![GitHub Repo](https://img.shields.io/badge/GitHub-agent47-181717?logo=github)](https://github.com/bmdhodl/agent47)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)

AgentGuard is a **zero-dependency** runtime guardrails toolkit for AI agents. Track costs per LLM call, catch loops, enforce dollar budgets, and replay failures deterministically — with nothing to install except one pure-Python package. No transitive supply chain risk. The SDK is open source; the hosted dashboard is the commercial layer.

## Why this exists
Multi-agent systems fail in ways normal software does not: infinite tool loops, silent cascade failures, and nondeterministic regressions. The current ecosystem is fragmented across model providers and frameworks. AgentGuard focuses on the runtime logic of agents, not the runtime engine.

## What is in this repo
- `sdk/` Open-source SDK (Python) with tracing, guards, evaluation, auto-instrumentation, async support, and replay.
- `dashboard/` Hosted dashboard (Next.js 14) — auth, Gantt viewer, billing, password management, security & help pages.
- `site/` Landing page with pricing, trust signals, FAQ, and security page.
- `scripts/` Deploy, demo, and test scripts.

## Features
- **Cost tracking**: dollar estimates per LLM call, per trace, per month (OpenAI, Anthropic, Gemini, Mistral)
- **Budget guards**: `BudgetGuard(max_cost_usd=5.00)` stops agents before they blow your API budget
- **Budget warnings**: `warn_at_pct=0.8` callback before hitting the limit
- **Loop detection**: exact match (`LoopGuard`) and fuzzy patterns (`FuzzyLoopGuard` — A-B-A-B alternation, same-tool frequency)
- **Rate limiting**: `RateLimitGuard(max_calls_per_minute=60)`
- **Async support**: `AsyncTracer`, `async_trace_agent`, `patch_openai_async`
- **Production hardening**: gzip compression, retry with backoff, 429 handling, idempotency keys, sampling, metadata
- **Evaluation as Code**: assertion-based trace analysis (`EvalSuite`)
- **Auto-instrumentation**: `@trace_agent` / `@trace_tool` decorators, OpenAI/Anthropic monkey-patches (sync + async)
- **Gantt trace viewer**: timeline visualization with XSS-safe rendering
- **Export**: JSON, CSV, JSONL conversion
- **Record and replay** runs to create deterministic tests
- **Hosted dashboard**: cost dashboard, Gantt timelines, loop/error alerts, usage tracking

## Install

```bash
pip install agentguard47
```

## Quickstart

```python
from agentguard import Tracer, BudgetGuard, LoopGuard, JsonlFileSink, patch_openai

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[LoopGuard(max_repeats=3), BudgetGuard(max_cost_usd=5.00)],
)
patch_openai(tracer)  # auto-tracks cost per call

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
    with span.span("tool.search"):
        pass  # your tool here
```

```bash
agentguard report traces.jsonl   # summary table
agentguard view traces.jsonl     # Gantt timeline in browser
```

## CLI

```bash
agentguard report traces.jsonl      # human-readable summary
agentguard view traces.jsonl        # Gantt trace viewer in browser
agentguard summarize traces.jsonl   # event-level breakdown
agentguard eval traces.jsonl        # run evaluation assertions
agentguard eval traces.jsonl --ci   # CI mode (exit code on failure)
```

## Hosted Dashboard

```python
from agentguard import Tracer, HttpSink

sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
tracer = Tracer(sink=sink, service="my-agent")
```

## MCP Server

AI agents can query their own observability data via MCP (Model Context Protocol):

```json
{
  "mcpServers": {
    "agentguard": {
      "command": "node",
      "args": ["./mcp-server/dist/index.js"],
      "env": { "AGENTGUARD_API_KEY": "ag_..." }
    }
  }
}
```

6 tools: `query_traces`, `get_trace`, `get_alerts`, `get_usage`, `get_costs`, `check_budget`. See `mcp-server/README.md` for details.

## Status

v0.8.0 (Beta) — 100+ tests, **zero dependencies** (pure Python stdlib), framework-agnostic. Full async support, production-hardened HttpSink, smarter guards.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, test commands, and PR guidelines. See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

SDK is MIT licensed (BMD PAT LLC). Dashboard is source-available (BSL 1.1).
