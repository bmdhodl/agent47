# Cost Tracking for LangGraph Agents

**Category:** Show and tell
**Labels:** langgraph, cost-control, budget

---

LangGraph agents can run for a long time — branching, backtracking, calling tools across multiple nodes. Without cost tracking, you have no idea what a graph execution costs until the OpenAI invoice arrives.

Here's how to add per-node budget enforcement to a LangGraph agent.

## The `guarded_node` decorator

AgentGuard provides a LangGraph-specific decorator that wraps any node with budget and loop guards:

```bash
pip install agentguard47[langgraph]
```

```python
from agentguard import Tracer, BudgetGuard, LoopGuard
from agentguard.integrations.langgraph import guarded_node

tracer = Tracer(service="my-graph-agent")
budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)

@guarded_node(tracer=tracer, budget_guard=budget)
def research_node(state):
    # Your LLM calls here
    return {"messages": state["messages"] + [result]}

@guarded_node(tracer=tracer, budget_guard=budget)
def synthesis_node(state):
    # More LLM calls
    return {"messages": state["messages"] + [summary]}
```

Every node execution is:
1. **Traced** — start/end events with timing
2. **Budget-checked** — if cumulative cost exceeds $5, `BudgetExceeded` is raised
3. **Loop-guarded** (optional) — catches repeated tool calls within the node

## What happens when the budget is exceeded

`BudgetExceeded` propagates up through the graph execution. You can catch it at the top level:

```python
from agentguard import BudgetExceeded

try:
    result = graph.invoke({"messages": [initial_message]})
except BudgetExceeded as e:
    print(f"Graph stopped: {e}")
    print(f"Total cost: ${budget.state.cost_used:.2f}")
    print(f"API calls: {budget.state.calls_used}")
```

The budget is shared across all nodes — so a $5 limit applies to the entire graph execution, not per-node.

## Adding the `guard_node` to your graph

For more control, you can add a standalone guard node that checks the budget between steps:

```python
from agentguard.integrations.langgraph import guard_node

# Create a guard node
budget_check = guard_node(budget_guard=budget)

# Add to your graph
graph.add_node("budget_check", budget_check)
graph.add_edge("research", "budget_check")
graph.add_edge("budget_check", "synthesis")
```

This checks the budget explicitly between the research and synthesis steps.

## Install

```bash
pip install agentguard47[langgraph]
```

Zero runtime dependencies in the core SDK. The LangGraph integration is an optional extra.

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)

---

*Anyone running LangGraph in production? Curious how you're handling cost tracking today.*
