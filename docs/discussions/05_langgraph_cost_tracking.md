# Cost Tracking for LangGraph Agents

> Tested bounds (2026-09-18): `guarded_node` charges `calls=1` at node entry.
> A dollar-only `BudgetGuard` does not fire from that wrapper. See
> [enforcement-boundary.md](../enforcement-boundary.md).

**Category:** Show and tell
**Labels:** langgraph, cost-control, budget

---

LangGraph agents can run for a long time — branching, backtracking, calling tools across multiple nodes. Without cost tracking, you have no idea what a graph execution costs until the OpenAI invoice arrives.

Here's how to add per-node call-budget enforcement to a LangGraph agent.

## The `guarded_node` decorator

AgentGuard provides a LangGraph-specific decorator that wraps any node with
tracing, an optional loop guard, and `consume(calls=1)` at entry:

```bash
pip install agentguard47[langgraph]
```

```python
from agentguard import Tracer, BudgetGuard, LoopGuard
from agentguard.integrations.langgraph import guarded_node

tracer = Tracer(service="my-graph-agent")
budget = BudgetGuard(max_calls=20)

@guarded_node(tracer=tracer, budget_guard=budget)
def research_node(state):
    messages = list(state.get("messages", []))
    messages.append("research complete")
    return {"messages": messages}

@guarded_node(tracer=tracer, budget_guard=budget)
def synthesis_node(state):
    messages = list(state.get("messages", []))
    messages.append("synthesis complete")
    return {"messages": messages}
```

Every node execution is:
1. **Traced** — start/end events with timing
2. **Call-budget checked** — if recorded calls already exceed `max_calls`, `BudgetExceeded` is raised before the node body
3. **Loop-guarded** (optional) — catches repeated identical node invocations

A dollar-only `BudgetGuard` does not fire from this wrapper. Patch inner
Chat Completions/Messages clients separately if you need recorded token or
cost preflight.

## What happens when the budget is exceeded

`BudgetExceeded` propagates up through the graph execution. You can catch it at the top level:

```python
from agentguard import BudgetExceeded

try:
    result = graph.invoke({"messages": [initial_message]})
except BudgetExceeded as e:
    print(f"Graph stopped: {e}")
    print(f"Recorded calls: {budget.state.calls_used}")
```

The call budget is shared across all nodes — so `max_calls=20` applies to the entire graph execution, not per-node. Token and dollar totals are not incremented by this wrapper.

## Adding `guard_node` at graph construction

Wrap an existing node function when you cannot use the decorator:

```python
from agentguard.integrations.langgraph import guard_node

graph.add_node(
    "research",
    guard_node(research_fn, tracer=tracer, budget_guard=budget),
)
```

That is the same `consume(calls=1)` entry check as `guarded_node`.

## Install

```bash
pip install agentguard47[langgraph]
```

Zero runtime dependencies in the core SDK. The LangGraph integration is an optional extra.

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)

---

*Anyone running LangGraph in production? Curious how you're handling cost tracking today.*
