# CrewAI Integration

The supported API is `AgentGuardCrewHandler`. There is no
`AgentGuardCrewCallback`.

`step_callback` runs **after** the agent step. Budget consume is advisory for
the step that just ran. The next callback can raise `BudgetExceeded`. See
[enforcement-boundary.md](../enforcement-boundary.md).

## Install

```bash
pip install agentguard47[crewai]
```

The `[crewai]` extra still carries unresolved ChromaDB advisories. Review
`#644` before installing it. Base installs do not include CrewAI.

## Quick Start

```python
from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.integrations.crewai import AgentGuardCrewHandler

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-crew",
)

handler = AgentGuardCrewHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=5),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

agent = Agent(
    role="researcher",
    step_callback=handler.step_callback,
)
```

## What Gets Traced

| CrewAI Event | AgentGuard Span/Event |
|---|---|
| Agent step | `step.<tool>` or `step.thought` span |
| Task callback | `task.complete` / related events |

## Viewing Traces

```bash
agentguard report traces.jsonl
```
