# LangGraph Integration

Wrap LangGraph node functions with tracing and runtime guards. The supported
API is `guarded_node` / `guard_node`. There is no `AgentGuardLangGraphCallback`.

`consume(calls=1)` runs at node entry. That is recorded-budget preflight for
the node, not a patch of inner provider clients. See
[enforcement-boundary.md](../enforcement-boundary.md).

## Install

```bash
pip install agentguard47[langgraph]
```

## Quick Start

```python
from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.integrations.langgraph import guarded_node

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-graph-agent",
)
budget = BudgetGuard(max_cost_usd=2.00)

@guarded_node(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=5),
    budget_guard=budget,
)
def research_node(state):
    return {"messages": state["messages"] + [result]}
```

Or wrap at graph construction time:

```python
from agentguard.integrations.langgraph import guard_node

builder.add_node("research", guard_node(research_fn, tracer=tracer, budget_guard=budget))
```

## What Gets Traced

| LangGraph Event | AgentGuard Span/Event |
|---|---|
| Node execution | `node.<name>` span |

Inner LLM calls are traced only if you also patch or wrap those clients.

## Guards in Graph Loops

`LoopGuard` detects when the same node runs with identical summarized state
too many times.

```bash
agentguard report traces.jsonl
```
