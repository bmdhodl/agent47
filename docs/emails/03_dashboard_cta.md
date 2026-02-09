# Email 3: Your Agents in Production — Dashboard CTA

**Send:** Day 7 after signup
**Subject:** Your agents are running in production. Are you watching?
**From:** AgentGuard <pat@bmdpat.com>

---

Hey,

If you're running AI agents in production (or about to), here's the question: what happens when something goes wrong at 2am?

Without observability, you find out from your users — or your AWS bill.

### What the AgentGuard Dashboard gives you

**Traces** — Every agent run as a Gantt timeline. Click any span to see inputs, outputs, cost, and duration.

**Alerts** — Get notified when agents hit budget limits, enter loops, or throw errors. Before your users do.

**Cost tracking** — See exactly how much each agent run costs. Per call, per trace, per month. Know your unit economics.

**Usage analytics** — Event volume, active traces, API key usage. All in one view.

### Free vs Pro

| | Free | Pro ($39/mo) |
|---|---|---|
| Events/month | 10,000 | 500,000 |
| Retention | 7 days | 30 days |
| API keys | 2 | 5 |

Most developers start on Free and upgrade when their agents hit production volume. No credit card required to start.

### Getting started takes 2 minutes

1. Sign up at app.agentguard47.com
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

— Pat, BMD PAT LLC

---

**CTA Button:** Start Free → https://app.agentguard47.com/signup
**Unsubscribe link:** Required at bottom
