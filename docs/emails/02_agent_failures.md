# Email 2: 3 Ways Agents Fail Silently

**Send:** Day 3 after signup
**Subject:** 3 ways your AI agents are failing (and you don't know it)
**From:** AgentGuard <hello@agentguard47.com>

---

Hey,

We've been watching how agents fail in production. There are 3 patterns that burn money and waste time — silently.

### 1. Infinite tool loops

Your agent calls the same tool with the same arguments, over and over. LangChain's `max_iterations` stops the agent eventually, but by then you've burned 50+ API calls.

**Fix with LoopGuard:**
```python
from agentguard import LoopGuard

guard = LoopGuard(max_repeats=3, window=6)
# Raises LoopDetected after 3 identical calls in a 6-call window
guard.check("search", tool_args={"query": "weather"})
```

### 2. Cost blowouts

One bad prompt can trigger a chain of expensive completions. A single GPT-4 agent run can cost $2-10. Run that 100 times in a batch job and you've got a surprise $500 bill.

**Fix with BudgetGuard:**
```python
from agentguard import BudgetGuard

guard = BudgetGuard(max_cost_usd=5.00)
guard.consume(cost_usd=0.12)  # tracks running total
# Raises BudgetExceeded when limit is hit
```

### 3. "It worked but did the wrong thing"

The agent returns a plausible-looking answer, but the intermediate steps are nonsense. Without tracing, you'd never know.

**Fix with structured tracing:**
```python
from agentguard import Tracer

tracer = Tracer(service="my-agent")
with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "checking docs..."})
    with span.span("tool.search"):
        # see every step in the Gantt timeline
        pass
```

All of these are caught automatically when you add AgentGuard. The SDK is 3 lines to set up and the dashboard shows you everything.

— The AgentGuard team

---

**CTA Button:** See it in action → https://app.agentguard47.com
**Unsubscribe link:** Required at bottom
