---
name: agentguard
description: Runtime budget / loop / timeout guards for AI coding agents. Stops runaway agents before they burn money.
license: MIT
pypi: agentguard47
source: https://github.com/bmdhodl/agent47
---

# AgentGuard (Codex skill)

Wrap any AI coding agent with runtime guards: budget, loop, timeout, rate-limit, retry. Zero dependencies, local-first.

## Trigger

Use when:
- Capping spend on an agent run
- Stopping infinite loops or A-B-A-B tool patterns
- Adding wall-clock timeouts
- Building termination semantics for production agents

Python only.

## Install

```bash
pip install agentguard47
agentguard doctor
```

## Quick start

```python
from agentguard import Tracer, BudgetGuard, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(service="my-agent")
patch_openai(tracer, budget_guard=budget)
```

At `$4`, `BudgetGuard` warns. At `$5`, it raises `BudgetExceeded` and the agent stops.

## Guards

- `BudgetGuard` — dollar / token / call caps
- `LoopGuard` — exact repeated tool calls
- `FuzzyLoopGuard` — similar / A-B-A-B patterns
- `TimeoutGuard` — wall-clock
- `RateLimitGuard` — calls per minute
- `RetryGuard` — retry storms

## Init from profile

```python
import agentguard
agentguard.init(profile="coding-agent", local_only=True)
```

Profiles: `coding-agent`, `deployed-agent`, `research-agent`. Override via `.agentguard.json`.

## Full reference

Canonical SKILL.md at repo root: <https://github.com/bmdhodl/agent47/blob/main/SKILL.md>

PyPI: <https://pypi.org/project/agentguard47/>
