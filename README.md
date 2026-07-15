# AgentGuard

**Stop runaway agents before they burn money.**

Zero-dependency Python kill switch for AI agents. Hard budget caps. Loop detection. Local traces. MIT.

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![Downloads](https://img.shields.io/pypi/dm/agentguard47)](https://pypi.org/project/agentguard47/)
[![Python](https://img.shields.io/pypi/pyversions/agentguard47)](https://pypi.org/project/agentguard47/)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

```bash
pip install agentguard47
```

## Getting started

### 1. Install and verify

```bash
pip install agentguard47
agentguard doctor   # package ok?
agentguard demo     # offline proof (no API keys)
```

### 2. Guard an OpenAI client

```python
from agentguard import BudgetGuard, LoopGuard, Tracer, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
loop = LoopGuard(max_repeats=3)
tracer = Tracer(service="my-agent", guards=[loop])

patch_openai(tracer, budget_guard=budget)
# every OpenAI call is now traced + budget-enforced
```

When spend crosses the hard limit, `BudgetExceeded` is raised and the run stops.

### 3. Cap a single task

Session budget can still have headroom. One goal can still be killed:

```python
with budget.goal("refund", max_cost_usd=0.50, warn_at_pct=0.8) as g:
    g.attempt()
    budget.consume(cost_usd=0.12)
    # BudgetExceeded names the goal when it crosses
```

### 4. Read the local proof

```bash
agentguard report .agentguard/traces.jsonl
agentguard incident .agentguard/traces.jsonl
```

Or scaffold a starter file:

```bash
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
```

## What it stops

| Problem | Guard | Exception |
|---------|-------|-----------|
| Spend blowup | `BudgetGuard` | `BudgetExceeded` |
| Same tool forever | `LoopGuard` | `LoopDetected` |
| Fuzzy / A-B-A-B loops | `FuzzyLoopGuard` | `LoopDetected` |
| Retry storms | `RetryGuard` | `RetryLimitExceeded` |
| Hung runs | `TimeoutGuard` | `TimeoutExceeded` |
| Spam calls | `RateLimitGuard` | — |

Not a dashboard. Not a model router. An **in-process exception** that kills the bad run mid-flight.

## Features

- **Hard stops** — exceptions inside your process, not after-the-fact alerts
- **Task-level budgets** — `BudgetGuard.goal(...)` for sub-task caps + warn hooks
- **Local traces** — JSONL by default; no network unless you opt in
- **Zero deps** — stdlib only; Python 3.9+
- **Provider patches** — `patch_openai` / `patch_anthropic`
- **Framework hooks** — LangChain, LangGraph, CrewAI (optional extras)

## Local by default

- No API key required for local proof
- No network unless you configure `HttpSink`
- MIT licensed

## Integrations

OpenAI · Anthropic · LangChain · LangGraph · CrewAI · raw agent loops

```bash
pip install "agentguard47[langchain]"   # optional extras as needed
```

## Docs

- [Getting started guide](docs/guides/getting-started.md)
- [Examples](examples/)
- [MCP server](mcp-server/) — `npx -y @agentguard47/mcp-server`

## Links

- PyPI: https://pypi.org/project/agentguard47/
- Issues: https://github.com/bmdhodl/agent47/issues

---

MIT · Built for people who ship agents and hate surprise bills.
