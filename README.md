# AgentGuard

[![GitHub Repo](https://img.shields.io/badge/GitHub-agent47-181717?logo=github)](https://github.com/bmdhodl/agent47)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)

AgentGuard is a lightweight observability and evaluation toolkit for multi-agent systems. It helps solo and small teams trace agent reasoning, catch loops, replay runs deterministically, and prevent runaway costs. The SDK is open source; the hosted dashboard is the commercial layer.

## Why this exists
Multi-agent systems fail in ways normal software does not: infinite tool loops, silent cascade failures, and nondeterministic regressions. The current ecosystem is fragmented across model providers and frameworks. AgentGuard focuses on the runtime logic of agents, not the runtime engine.

## What is in this repo
- `docs/` Product strategy, PRD, architecture, pricing, and metrics.
- `sdk/` Open-source SDK (Python) with tracing, guards, and replay primitives.
- `docs/examples/` Integration examples (starting with LangChain).
- `docs/trace_schema.md` Trace event schema for JSONL output.
- `site/` Minimal landing page for early users.

## MVP scope
- Trace agent reasoning steps and tool calls with correlation IDs
- Detect common loop patterns and stop runaway executions
- Record and replay runs to create deterministic tests
- JSONL export for local inspection (future: hosted dashboard)

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

# open trace viewer in browser
agentguard view traces.jsonl

# summarize events
agentguard summarize traces.jsonl
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

## Status

Early build. The SDK is intentionally minimal and framework-agnostic. See `docs/prd.md` for roadmap.
