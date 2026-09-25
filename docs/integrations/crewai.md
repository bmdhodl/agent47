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

The optional extra pulls ChromaDB. The
[2026-09-12 audit](../../proof/audit-20260912/README.md) resolved CrewAI 1.15.21
with ChromaDB 1.1.1 and recorded four unresolved advisories:
CVE-2026-45829 (PYSEC-2026-311), CVE-2026-45830, CVE-2026-45831, and
CVE-2026-45833. The audit found no fixed release at that time.

[CVE-2026-45829](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c) concerns
code injection through the ChromaDB Python server. Review the upstream
advisories and your deployment exposure before installing this extra.
AgentGuard does not fix these dependencies; tracking issue:
[#644](https://github.com/bmdhodl/agent47/issues/644). Base SDK installs do not include
ChromaDB.

## Quick Start

```python
from crewai import Agent
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
    goal="Answer one short question clearly.",
    backstory="You are concise and careful.",
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
