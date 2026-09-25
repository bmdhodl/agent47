---
name: agentguard
description: Runtime guardrails for AI coding agents. Recorded-budget preflight, loop, retry, and timeout checks in instrumented Python. Zero dependencies, local-first, MIT licensed.
license: MIT
compatibility: Requires Python 3.9+
metadata:
  author: bmdhodl
  version: "1.4.1"
  pypi: agentguard47
---

# AgentGuard

Runtime guardrails for coding agents. Recorded-budget preflight, loops, retries, and timeouts on instrumented Python paths. Zero dependencies. Local-first. This skill is onboarding, not host enforcement. See docs/enforcement-boundary.md.

## Install

```bash
pip install agentguard47
```

Verify the install:

```bash
agentguard doctor
```

## Quick Start (4 lines)

```python
from agentguard import Tracer, BudgetGuard, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(service="support-agent")
patch_openai(tracer, budget_guard=budget)
# Chat Completions are tracked. Exhausted recorded budget refuses the next dispatch.
```

## Guards

| Guard | What it stops | Example |
|-------|--------------|---------|
| `BudgetGuard` | Dollar/token/call overruns | `BudgetGuard(max_cost_usd=5.00)` |
| `LoopGuard` | Exact repeated tool calls | `LoopGuard(max_repeats=3)` |
| `FuzzyLoopGuard` | Similar calls, A-B-A-B patterns | `FuzzyLoopGuard(max_tool_repeats=5)` |
| `TimeoutGuard` | Wall-clock time limits | `TimeoutGuard(max_seconds=300)` |
| `RateLimitGuard` | Calls-per-minute throttling | `RateLimitGuard(max_calls_per_minute=60)` |
| `RetryGuard` | Retry storms on flaky tools | `RetryGuard(max_retries=3)` |

Guards raise exceptions (`BudgetExceeded`, `LoopDetected`, `TimeoutExceeded`, `RetryLimitExceeded`) on instrumented paths. They do not intercept host tools or provider invoices.

## One-Liner Init with Defaults

```python
import agentguard

agentguard.init(local_only=True)
# Reads .agentguard.json if present, sets up tracer + budget guard with sensible defaults
```

Or drop a `.agentguard.json` in your repo root:

```json
{
  "profile": "coding-agent",
  "service": "my-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

## Tracing

```python
from agentguard import Tracer, JsonlFileSink, BudgetGuard

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    guards=[BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "search docs"})
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
```

## Auto-Instrumentation

```python
from agentguard import Tracer, BudgetGuard, patch_openai, patch_anthropic

budget = BudgetGuard(max_cost_usd=5.00)
tracer = Tracer(service="support-agent")
patch_openai(tracer, budget_guard=budget)      # tracks ChatCompletion calls
patch_anthropic(tracer, budget_guard=budget)   # tracks Messages calls
```

## Framework Integrations

LangChain, LangGraph, and CrewAI are supported as optional extras:

```bash
pip install agentguard47[langchain]
pip install agentguard47[langgraph]
pip install agentguard47[crewai]
```

## CLI Tools

```bash
agentguard doctor              # verify install, no network calls
agentguard demo                # local proof run, no API keys needed
agentguard report traces.jsonl # summarize a trace file
agentguard eval traces.jsonl   # assert properties in CI
agentguard incident traces.jsonl --format html  # postmortem report
```

## Links

- PyPI: https://pypi.org/project/agentguard47/
- GitHub: https://github.com/bmdhodl/agent47
- Docs: https://github.com/bmdhodl/agent47/tree/main/docs
- Enforcement boundary: https://github.com/bmdhodl/agent47/blob/main/docs/enforcement-boundary.md
- Dashboard: https://app.agentguard47.com
