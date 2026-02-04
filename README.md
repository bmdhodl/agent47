# AgentGuard

[![GitHub Repo](https://img.shields.io/badge/GitHub-agent47-181717?logo=github)](https://github.com/bmdhodl/agent47)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AgentGuard is a lightweight observability and evaluation toolkit for multi-agent systems. It helps solo and small teams trace agent reasoning, catch loops, replay runs deterministically, and prevent runaway costs. The SDK is open source; the hosted dashboard is the commercial layer.

Repo: https://github.com/bmdhodl/agent47

This repo starts the business from first principles: product strategy, go-to-market, and a working SDK skeleton.

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

## Quickstart (local SDK)
```bash
python3 -m pip install -e /Users/patrickhughes/Documents/New\\ project/sdk
python3 -m agentguard.cli summarize /Users/patrickhughes/Documents/New\\ project/sample_traces.jsonl
```

## Getting started (builders)
```bash
# install SDK
python3 -m pip install -e /Users/patrickhughes/Documents/New\\ project/sdk

# run demo
python3 /Users/patrickhughes/Documents/New\\ project/sdk/examples/demo_agent.py

# view report
python3 -m agentguard.cli report /Users/patrickhughes/Documents/New\\ project/sdk/examples/traces.jsonl
```

## Demo (fast momentum)
```bash
python3 /Users/patrickhughes/Documents/New\\ project/sdk/examples/demo_agent.py
python3 -m agentguard.cli summarize /Users/patrickhughes/Documents/New\\ project/sdk/examples/traces.jsonl
```

## One-command demo
```bash
/Users/patrickhughes/Documents/New\\ project/run_demo.sh
```

## Launch assets
- Draft post copy: `docs/launch_post.md`
- Local screenshots: `site_screenshots/`

## What the report means
The report summarizes a single agent run:
- `Total events`: total trace records emitted
- `Spans` vs `Events`: span start/end records vs in-run events
- `Approx run time`: duration of the run (ms)
- `Reasoning steps`: how many reasoning events were logged
- `Tool results`: tool call outputs captured
- `LLM results`: model outputs captured
- `Loop guard triggered`: how many times a repeated-call loop was detected

## Business principle
Service-as-Software: sell outcomes, not tooling. AgentGuard's paid layer is a hosted dashboard and team features; the SDK is MIT and designed for self-serve adoption.

## Status
Early build. The SDK is intentionally minimal and framework-agnostic. Next steps are in `docs/prd.md`.
