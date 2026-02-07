# AgentGuard

[![GitHub Repo](https://img.shields.io/badge/GitHub-agent47-181717?logo=github)](https://github.com/bmdhodl/agent47)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)

AgentGuard is a **zero-dependency** observability and runtime guard toolkit for AI agents. Trace reasoning steps, catch loops, enforce budgets, and replay runs deterministically — with nothing to install except one pure-Python package. No transitive supply chain risk. The SDK is open source; the hosted dashboard is the commercial layer.

## Why this exists
Multi-agent systems fail in ways normal software does not: infinite tool loops, silent cascade failures, and nondeterministic regressions. The current ecosystem is fragmented across model providers and frameworks. AgentGuard focuses on the runtime logic of agents, not the runtime engine.

## What is in this repo
- `sdk/` Open-source SDK (Python) with tracing, guards, evaluation, auto-instrumentation, and replay.
- `docs/strategy/` Product strategy, PRD, architecture, pricing, and metrics.
- `docs/examples/` Integration examples (starting with LangChain).
- `docs/strategy/trace_schema.md` Trace event schema for JSONL output.
- `dashboard/` Hosted dashboard (Next.js 14) — auth, Gantt viewer, billing, password management, security & help pages.
- `site/` Landing page with pricing, trust signals, FAQ, and security page.
- `scripts/` Deploy, demo, and test scripts.

## Features
- Trace agent reasoning steps and tool calls with correlation IDs
- Detect common loop patterns and stop runaway executions
- Record and replay runs to create deterministic tests
- Evaluation as Code: assertion-based trace analysis (`EvalSuite`)
- Auto-instrumentation: `@trace_agent` / `@trace_tool` decorators, OpenAI/Anthropic monkey-patches
- Gantt trace viewer: timeline visualization with click-to-expand details
- JSONL export for local inspection
- Hosted dashboard: send traces via HttpSink, view Gantt timelines in the browser

## Install

```bash
pip install agentguard47
```

With LangChain support:
```bash
pip install agentguard47[langchain]
```

## Quickstart (2 minutes)

**1. Install:**
```bash
pip install agentguard47
```

**2. Trace your agent:**
```python
from agentguard import Tracer, LoopGuard
from agentguard.tracing import JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
guard = LoopGuard(max_repeats=3)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
    guard.check(tool_name="search", tool_args={"query": "agent loops"})
    with span.span("tool.search"):
        pass  # your tool here
    span.event("llm.result", data={"answer": "done"})
```

**3. See what happened:**
```bash
agentguard report traces.jsonl   # summary table
agentguard view traces.jsonl     # Gantt timeline in browser
```

That's it. You get a structured JSONL trace and a visual timeline. No config, no dependencies, no account needed.

## CLI

```bash
agentguard report traces.jsonl      # human-readable summary
agentguard view traces.jsonl        # Gantt trace viewer in browser
agentguard summarize traces.jsonl   # event-level breakdown
agentguard eval traces.jsonl        # run evaluation assertions
```

## What the report means

The report summarizes a single agent run:
- `Total events`: total trace records emitted
- `Spans` vs `Events`: span start/end records vs in-run events
- `Approx run time`: duration of the run (ms)
- `Reasoning steps`: how many reasoning events were logged
- `Tool results` / `LLM results`: captured outputs
- `Loop guard triggered`: repeated-call loops detected

## Hosted Dashboard

Send traces to the hosted dashboard instead of local files:

```python
from agentguard import Tracer
from agentguard.sinks.http import HttpSink

sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
tracer = Tracer(sink=sink, service="my-agent")
```

The dashboard provides Gantt timelines, loop/error alerts, usage tracking, and team management. Free tier: 10K events/month. See [pricing](https://agentguard47.com#pricing).

## Status

v0.4.0 — 49 tests, **zero dependencies** (pure Python stdlib), framework-agnostic. See `docs/strategy/prd.md` for roadmap.
