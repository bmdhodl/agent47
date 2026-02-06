# AgentGuard

[![GitHub Repo](https://img.shields.io/badge/GitHub-agent47-181717?logo=github)](https://github.com/bmdhodl/agent47)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)

AgentGuard is a lightweight observability and evaluation toolkit for multi-agent systems. It helps solo and small teams trace agent reasoning, catch loops, replay runs deterministically, and prevent runaway costs. The SDK is open source; the hosted dashboard is the commercial layer.

## Why this exists
Multi-agent systems fail in ways normal software does not: infinite tool loops, silent cascade failures, and nondeterministic regressions. The current ecosystem is fragmented across model providers and frameworks. AgentGuard focuses on the runtime logic of agents, not the runtime engine.

## What is in this repo
- `sdk/` Open-source SDK (Python) with tracing, guards, evaluation, auto-instrumentation, and replay.
- `docs/strategy/` Product strategy, PRD, architecture, pricing, and metrics.
- `docs/examples/` Integration examples (starting with LangChain).
- `docs/strategy/trace_schema.md` Trace event schema for JSONL output.
- `dashboard/` Hosted dashboard (Next.js 14) — auth, Gantt viewer, billing.
- `site/` Landing page with pricing.
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

## Quickstart

```python
from agentguard import Tracer, LoopGuard

tracer = Tracer()
guard = LoopGuard(max_repeats=3)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
    guard.check(tool_name="search", tool_args={"query": "agent loops"})
    with span.span("tool.call", data={"tool": "search"}):
        pass  # your tool here
```

## CLI

```bash
# human-readable report
agentguard report traces.jsonl

# open Gantt trace viewer in browser
agentguard view traces.jsonl

# summarize events
agentguard summarize traces.jsonl

# run evaluation assertions
agentguard eval traces.jsonl
```

## Run the demo

```bash
pip install -e ./sdk
python3 sdk/examples/demo_agent.py
agentguard report sdk/examples/traces.jsonl
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

sink = HttpSink(url="https://app.agentguard.dev/api/ingest", api_key="ag_...")
tracer = Tracer(sink=sink, service="my-agent")
```

The dashboard provides Gantt timelines, loop/error alerts, usage tracking, and team management. Free tier: 10K events/month. See [pricing](https://agentguard.dev#pricing).

## Status

v0.3.0 — 48 tests, zero-dependency, framework-agnostic. See `docs/strategy/prd.md` for roadmap.
