# How to Limit OpenAI API Spend Per Agent Run

**Category:** Show and tell
**Labels:** openai, budget, cost-control

---

If you're running autonomous agents with OpenAI, you've probably wondered: how do I set a hard dollar limit per agent run?

OpenAI has account-level spend limits, but those are a kill switch for your entire organization. They don't help when one agent run out of 50 goes haywire.

Here's how to set a per-run budget that kills the agent the moment it exceeds your limit.

## Setup

```bash
pip install agentguard47
```

```python
from agentguard import Tracer, BudgetGuard, BudgetExceeded, patch_openai

tracer = Tracer(
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=2.00, warn_at_pct=0.8)],
)
patch_openai(tracer)

# Now use OpenAI normally:
import openai
client = openai.OpenAI()

try:
    for i in range(100):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Step {i}: analyze data"}],
        )
except BudgetExceeded as e:
    print(f"Agent stopped: {e}")
    # Agent killed at $2.00 — no more API calls
```

`patch_openai` intercepts every `ChatCompletion` response, extracts token counts, estimates cost using published pricing, and feeds it into BudgetGuard. When the cumulative cost exceeds your limit, `BudgetExceeded` is raised.

## Warning before the hard stop

The `warn_at_pct=0.8` parameter fires a callback at 80% of the budget. You can use this for graceful shutdown:

```python
guard = BudgetGuard(
    max_cost_usd=5.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"WARNING: {msg}"),
)
```

## Zero dependencies

AgentGuard is pure Python stdlib. No extra packages to audit.

```bash
pip install agentguard47
```

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)

---

*What's your current approach to limiting per-agent spend? Curious if anyone has built custom solutions.*
