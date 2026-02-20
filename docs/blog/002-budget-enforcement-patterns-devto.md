---
title: "3 Patterns for Enforcing AI Agent Budgets in Python"
published: true
tags: [ai, python, openai, budgets]
description: "Hard dollar caps, warning callbacks, and auto-tracking — three patterns to stop runaway agent costs."
canonical_url: https://github.com/bmdhodl/agent47/blob/main/docs/blog/002-budget-enforcement-patterns-devto.md
---

"How do I stop my agent from spending more than $X?"

OpenAI's API doesn't have per-request budget caps. Account-level spend limits are a blunt instrument — they kill everything, not just the runaway agent. And by the time the limit kicks in, you've already spent the money.

Here are three patterns for enforcing budgets at the agent level, from simplest to most automated.

## Pattern 1: Hard Dollar Cap

Stop execution the moment cost exceeds a threshold:

```python
from agentguard import BudgetGuard, BudgetExceeded

guard = BudgetGuard(max_cost_usd=2.00)

# After each LLM call, feed in the cost:
guard.consume(tokens=1500, cost_usd=0.045)

# When cumulative cost exceeds $2.00 → BudgetExceeded raised
```

Set a dollar amount. Call `consume()` after each API call. Catch the exception. Done.

## Pattern 2: Warning Before the Limit

Get a heads-up at 80% so you can gracefully wrap up:

```python
from agentguard import BudgetGuard, BudgetExceeded

wrapping_up = False

def on_budget_warning(msg):
    global wrapping_up
    wrapping_up = True
    print(f"Budget warning: {msg}")

guard = BudgetGuard(
    max_cost_usd=5.00,
    warn_at_pct=0.8,
    on_warning=on_budget_warning,
)

for step in range(100):
    try:
        guard.consume(cost_usd=0.12)
    except BudgetExceeded:
        print("Hard stop — budget exceeded")
        break

    if wrapping_up:
        break  # Finish current task, skip new tool calls
```

Two-phase shutdown: `on_warning` fires at 80%, `BudgetExceeded` is the hard stop.

## Pattern 3: Auto-Tracking with OpenAI Patching

Skip manual `consume()` calls entirely — let AgentGuard estimate cost automatically:

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink, patch_openai

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=5.00)],
)
patch_openai(tracer)

# Every OpenAI call is now auto-traced with cost estimates.
# BudgetGuard checks after each call.
# Supports GPT-4o, GPT-4, GPT-3.5, and embedding models.
```

`patch_openai` intercepts `ChatCompletion` responses, extracts token counts from the response, and feeds them into BudgetGuard. No manual tracking.

Works with Anthropic too:

```python
from agentguard import patch_anthropic
patch_anthropic(tracer)
```

## Combining with Loop Detection

Budget overruns and loops often go together. A stuck agent burns through your budget fast. Layer both guards:

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[
        LoopGuard(max_repeats=3),
        BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8),
    ],
)
```

Whichever guard triggers first stops the agent.

## Which Pattern to Use

- **Pattern 1** — quick scripts, one-off runs, prototypes
- **Pattern 2** — production agents that need graceful shutdown
- **Pattern 3** — any project using OpenAI/Anthropic SDKs directly

All three work with zero dependencies. Pattern 3 adds auto-instrumentation, so you never forget to track a call.

## Try It

```bash
pip install agentguard47
python examples/try_it_now.py
```

Zero config, no API keys needed to see BudgetGuard in action.

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)
