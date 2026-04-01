# Email 3: Your Agents in Production - Dashboard CTA

**Send:** Day 7 after signup
**Subject:** Your agents are running in production. Are you watching?
**From:** AgentGuard <pat@bmdpat.com>

---

Hey,

If you're running AI agents in production, here's the real question: what
happens when something goes wrong at 2am?

Without retained history or alerts, you find out from users or from the bill.

### What the hosted dashboard adds

**Retained traces** - agent runs stay visible after the local file is gone.

**Alerts** - know when agents hit budget limits, enter loops, or throw errors.

**Operational follow-through** - see incidents over time instead of one local
trace at a time.

### Why the SDK still comes first

AgentGuard is designed to prove itself locally first:
- `agentguard doctor`
- `agentguard demo`
- local traces and incident reports

Once that path is working, the hosted dashboard is the place for retained
history, alerts, and team-visible operations.

### Getting started takes 2 minutes

1. Open app.agentguard47.com
2. Create an API key in Settings
3. Point your SDK's HttpSink at the ingest endpoint

```python
from agentguard.sinks.http import HttpSink

sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_your_key_here"
)
```

That's it. Traces start flowing immediately.

- Pat, BMD PAT LLC

---

**CTA Button:** Open Dashboard -> https://app.agentguard47.com/
**Unsubscribe link:** Required at bottom
