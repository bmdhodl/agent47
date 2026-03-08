# AgentGuard — North Star

## What it is

An open-source Python SDK + hosted dashboard that gives AI teams cost control over their agents — hard budget limits, loop detection, spend visibility, and policy management that stop runaway AI bills before they happen.

**SDK:** Zero-dependency runtime guards that kill agents mid-run when they exceed spend limits.
**Dashboard:** The hosted control surface — see spend, set limits, get alerts when things go wrong.

## Who it's for

Small AI teams (1-10 engineers) building autonomous agent systems with LangChain, LangGraph, CrewAI, or raw OpenAI/Anthropic APIs — especially those moving agents from prototype to production and needing predictable AI costs.

## What problem it solves

Agents fail silently. They loop, overspend, and hang. AgentGuard intercepts these failures at runtime with hard budget caps, loop detection, and timeout enforcement. The hosted dashboard gives teams spend visibility and policy management without building infrastructure.

## Non-goals

1. **Not a framework.** We don't orchestrate agents. We guard whatever framework you already use.
2. **Not a full observability platform.** We are not LangSmith, Langfuse, or Helicone. We don't do prompt management, eval suites, or deep trace exploration. We control costs and stop runaways.
3. **Not a prompt engineering tool.** We don't evaluate prompt quality or optimize outputs. We stop agents from burning money and looping.
4. **Not enterprise governance.** No RBAC, audit logs, or compliance features in V1. We serve small teams first.
