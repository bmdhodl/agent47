# Email 1: Welcome + Quickstart

**Send:** Immediately on signup (Day 0)
**Subject:** You're in — here's how to get your first trace in 60 seconds
**From:** AgentGuard <hello@agentguard47.com>

---

Hey,

Thanks for signing up for AgentGuard updates.

Here's the fastest way to see what your agents are actually doing:

```bash
pip install agentguard47
```

```python
from agentguard import Tracer, BudgetGuard
from agentguard.sinks.http import HttpSink

sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
tracer = Tracer(sink=sink, service="my-agent")
guard = BudgetGuard(max_cost_usd=5.00)

with tracer.trace("agent.run") as span:
    # your agent code here
    pass
```

That's it. Your traces show up in the dashboard within seconds.

**What you get right now (free tier):**
- 10,000 events/month
- 7-day retention
- Loop detection, budget enforcement, cost tracking
- Gantt timeline visualization

The SDK is MIT-licensed with zero dependencies — nothing to audit, nothing that can break.

If you're using LangChain, we have a drop-in callback handler too. Just `pip install agentguard47[langchain]`.

Questions? Reply to this email.

— The AgentGuard team

---

**CTA Button:** Open Dashboard → https://app.agentguard47.com
**Unsubscribe link:** Required at bottom
