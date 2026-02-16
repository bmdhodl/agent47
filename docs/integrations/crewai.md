# CrewAI Integration

AgentGuard integrates with CrewAI to trace crew task execution and agent interactions.

## Install

```bash
pip install agentguard47[crewai]
```

## Quick Start

```python
from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.integrations.crewai import AgentGuardCrewCallback

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-crew",
)

callback = AgentGuardCrewCallback(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=5),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)
```

## What Gets Traced

| CrewAI Event | AgentGuard Span/Event |
|---|---|
| Task execution | `task.<description>` span |
| Agent action | `agent.<role>` span |
| Tool use | `tool.<name>` event |

## With a Crew

```python
from crewai import Agent, Task, Crew

researcher = Agent(role="Researcher", goal="...", backstory="...")
writer = Agent(role="Writer", goal="...", backstory="...")

task = Task(description="Research and write about X", agent=researcher)
crew = Crew(agents=[researcher, writer], tasks=[task])

result = crew.kickoff(callbacks=[callback])
```

## Budget Control for Multi-Agent Teams

CrewAI crews can involve multiple agents making many LLM calls. BudgetGuard prevents runaway costs across the entire crew execution.

```bash
agentguard report traces.jsonl
```
