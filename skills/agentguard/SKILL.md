---
name: agentguard
description: Runtime guardrails for AI coding agents. Stop loops, budget overruns, retry storms, and timeouts before they burn money. Zero dependencies, local-first, MIT licensed.
license: MIT
compatibility: Requires Python 3.9+
metadata:
  author: bmdhodl
  version: "1.2.7"
  pypi: agentguard47
  source: https://github.com/bmdhodl/agent47
---

# AgentGuard (Claude Code skill)

Runtime guardrails for AI coding agents. Wraps any agent (OpenAI, Anthropic, LangChain, LangGraph, CrewAI) with budget, loop, timeout, rate-limit, and retry guards that raise exceptions when limits trip. Zero dependencies, local-first, no telemetry.

## When to use this skill

Trigger this skill when:

- The user asks to "cap AI costs", "stop runaway agents", "prevent infinite loops", "set a budget on an agent", "kill agents that loop", or anything in that family.
- The user is writing or operating an autonomous agent (single-turn or multi-turn) and has not yet wrapped it in spend / loop / timeout protection.
- The user reports an incident where an agent exceeded budget, looped, or burned tokens unexpectedly.
- The user is shipping an agent to production and has no runtime termination semantics.

Do NOT trigger this skill for:

- Static prompt-engineering questions (no runtime).
- Non-Python stacks (AgentGuard is Python-only today).

## Install

```bash
pip install agentguard47
agentguard doctor   # verify install, no network calls
```

## Minimal init (4 lines)

```python
from agentguard import Tracer, BudgetGuard, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(service="my-agent")
patch_openai(tracer, budget_guard=budget)
# OpenAI chat completions are now tracked. At $4 -> warn. At $5 -> raise BudgetExceeded.
```

## Guards available

| Guard | Stops |
|---|---|
| `BudgetGuard` | Dollar / token / call overruns |
| `LoopGuard` | Exact repeated tool calls |
| `FuzzyLoopGuard` | Similar calls, A-B-A-B patterns |
| `TimeoutGuard` | Wall-clock time limits |
| `RateLimitGuard` | Calls-per-minute throttling |
| `RetryGuard` | Retry storms on flaky tools |

Each raises a specific exception (`BudgetExceeded`, `LoopDetected`, `TimeoutExceeded`, `RetryLimitExceeded`) so the agent stops immediately.

## One-liner with profile

```python
import agentguard
agentguard.init(profile="coding-agent", local_only=True)
```

Profiles: `coding-agent`, `deployed-agent`, `research-agent`, custom via `.agentguard.json` in repo root.

## CLI

```bash
agentguard doctor                      # verify install
agentguard demo                        # local proof run, no API keys
agentguard report traces.jsonl         # summarize a trace file
agentguard eval traces.jsonl           # CI assertions
agentguard incident traces.jsonl --format html
```

## Full reference

See the canonical `SKILL.md` at the repo root: <https://github.com/bmdhodl/agent47/blob/main/SKILL.md>

## Links

- PyPI: <https://pypi.org/project/agentguard47/>
- Source: <https://github.com/bmdhodl/agent47>
- Docs: <https://github.com/bmdhodl/agent47/tree/main/docs>
