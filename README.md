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
| Wallet drain (x402/USDC) | `X402SpendGuard` | `BudgetExceeded` |

Not a dashboard. Not a model router. An **in-process exception** that kills the bad run mid-flight.

### Cap your agent's x402 wallet spend

Agents that pay per-call via x402 (USDC micropayments) can drain a wallet in a
silent loop. `X402SpendGuard` wraps the payment step and refuses before paying:

```python
from agentguard import X402SpendGuard

guard = X402SpendGuard(
    max_total_usd=5.00,        # wallet cap, add period="day" for a daily reset
    max_per_endpoint_usd=1.00, # cap per resource URL
    max_per_call_usd=0.10,     # refuse any single payment above this
)
guard.charge(0.001, "https://api.example.com/search", my_x402_pay_step)
```

AgentGuard meters and refuses; it never signs or settles. Amounts come from
your x402 client. No crypto dependencies.

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

The SDK is the free local proof path. Start local. Add hosted ingest later only if you want retained history, alerts, team visibility, spend trends, hosted decision history, or dashboard-managed remote kill signals. Local guards remain authoritative. `HttpSink` mirrors trace and decision events; it does not execute remote kill signals by itself.

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
- AgentGuard on the web (hosted history, alerts, and MCP visibility for Claude Code, Cursor, and Codex): https://bmdpat.com/tools/agentguard?utm_source=agentguard47&utm_medium=readme&utm_campaign=touchpoints

The hosted page is an optional next step, not a requirement. The SDK stays free, local, and MIT, and the local guards stay authoritative. Nothing in this package phones home. The only network egress is a sink or exporter you configure yourself, such as `HttpSink` or an OpenTelemetry exporter.

---

MIT · Built for people who ship agents and hate surprise bills.
