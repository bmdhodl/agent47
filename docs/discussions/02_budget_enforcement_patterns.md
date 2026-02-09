# Budget Enforcement Patterns for OpenAI API Calls

**Category:** Show and tell
**Labels:** budget, cost-control, openai, guides

---

One of the most common questions I see in agent repos: "How do I stop my agent from spending more than $X?"

OpenAI's API doesn't have a per-request budget cap. You can set spend limits at the account level, but that's a blunt instrument — it kills everything, not just the runaway agent. And by the time the limit kicks in, you've already spent the money.

Here are three patterns for enforcing budgets at the agent level.

## Pattern 1: Hard dollar cap per run

Stop execution the moment estimated cost exceeds a threshold:

```python
from agentguard import BudgetGuard, BudgetExceeded

guard = BudgetGuard(max_cost_usd=2.00)

# After each LLM call, feed in the token count:
guard.consume(tokens=1500, cost_usd=0.045)

# When cumulative cost exceeds $2.00, raises BudgetExceeded
```

This is the simplest pattern. Set a dollar amount, consume after each call, catch the exception.

## Pattern 2: Warning before the limit

Get a heads-up at 80% of the budget so you can gracefully wrap up:

```python
from agentguard import BudgetGuard, BudgetWarning, BudgetExceeded

guard = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)

try:
    guard.consume(cost_usd=4.10)  # crosses 80% threshold
except BudgetWarning:
    # 80% of budget used — tell the agent to wrap up
    print("Budget warning: finishing current task, no new tool calls")
except BudgetExceeded:
    # Hard stop
    print("Budget exceeded, stopping execution")
```

This lets you build a two-phase shutdown: soft warning first, then hard stop.

## Pattern 3: Auto-tracking with OpenAI patching

Skip manual `consume()` calls — let AgentGuard estimate cost automatically:

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink, patch_openai

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=5.00)],
)
patch_openai(tracer)

# Every OpenAI call is now auto-traced with cost estimates.
# BudgetGuard checks the budget after each call.
# Supports GPT-4, GPT-3.5, and embedding models.
```

The cost estimates use published token pricing. You can override prices for custom or fine-tuned models:

```python
from agentguard import update_prices

update_prices({"my-fine-tuned-model": {"input": 0.003, "output": 0.006}})
```

## Combining with loop detection

Budget overruns and loops often go together. An agent stuck in a loop burns through your budget fast. Layer both guards:

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

Whichever guard triggers first stops the agent. The loop guard catches pathological repeats; the budget guard catches legitimate-but-expensive runs.

## Install

```bash
pip install agentguard47
```

Zero dependencies, MIT licensed, Python 3.9+.

Repo: https://github.com/bmdhodl/agent47

---

*What's your current approach to budget enforcement? Curious if anyone's built custom solutions or run into edge cases.*
