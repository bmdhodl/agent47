# LangGraph Integration

AgentGuard integrates with LangGraph to trace graph node execution with runtime guards.

## Install

```bash
pip install agentguard47[langgraph]
```

## Quick Start

```python
from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.integrations.langgraph import AgentGuardLangGraphCallback

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-graph-agent",
)

callback = AgentGuardLangGraphCallback(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=5),
    budget_guard=BudgetGuard(max_cost_usd=2.00),
)
```

## What Gets Traced

| LangGraph Event | AgentGuard Span/Event |
|---|---|
| Node execution | `node.<name>` span |
| Edge traversal | `edge.<source>_to_<target>` event |
| Graph start/end | `graph.<name>` span |

## With StateGraph

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_edge("research", "write")
graph.add_edge("write", END)

app = graph.compile()
result = app.invoke(
    {"messages": [HumanMessage(content="...")]},
    config={"callbacks": [callback]},
)
```

## Guards in Graph Loops

LangGraph graphs often have cycles (e.g., agent loops). AgentGuard's LoopGuard detects when the same node executes with identical state too many times, preventing infinite loops.

```bash
agentguard report traces.jsonl
```
