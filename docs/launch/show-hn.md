# Show HN Launch Plan

## Post Title

```
Show HN: AgentGuard - runtime guardrails for coding agents (Python, MIT, zero deps)
```

## Post URL

```
https://github.com/bmdhodl/agent47
```

## Post Text

```
Hi HN,

I built AgentGuard after spending too much time debugging the same coding-agent failure modes:

- the agent retries the same flaky tool forever
- it loops through the same shell call or search step
- it quietly burns budget while looking "busy"

Most tools show nice traces after the fact. AgentGuard is meant to stop the run while it's still happening.

What it does:

- BudgetGuard: hard dollar budgets with warnings before the ceiling
- LoopGuard: catches repeated tool calls and simple alternation patterns
- RetryGuard: stops retry storms on the same flaky tool
- Local tracing + reports: JSONL traces, incident reports, and eval assertions

What I cared about technically:

- zero dependencies in the core SDK
- local-first setup
- no API keys required for the first proof
- works with raw Python, OpenAI, Anthropic, LangChain, LangGraph, or CrewAI
- MIT licensed

The quickest way to try it is:

    pip install agentguard47
    agentguard doctor
    agentguard demo
    python examples/demo_budget_kill.py

That path stays local, writes traces, and proves the SDK can stop runaway
spend before the agent burns more budget.

I also ship a small MCP server for coding agents that want to inspect retained traces later:

    npx -y @agentguard47/mcp-server

The goal is pretty narrow: stop coding agents from looping, retrying forever, and burning budget.

GitHub: https://github.com/bmdhodl/agent47
PyPI: https://pypi.org/project/agentguard47/
```

## Timing

- Best days: Monday-Wednesday
- Best time: 8-10 AM ET
- Avoid: Fridays, weekends, holidays

## Pre-Launch Checklist

- [ ] `pip install agentguard47==<release-version>` works for the tag being shipped
- [ ] `agentguard doctor` works from a clean virtualenv
- [ ] `agentguard demo` works without API keys
- [ ] `python examples/demo_budget_kill.py` works without API keys
- [ ] All README links resolve
- [ ] MCP package still resolves from npm: `npx -y @agentguard47/mcp-server`
- [ ] README, PyPI description, and MCP README tell the same story
- [ ] One short GIF or terminal clip is ready

## Post-Launch (first 4 hours)

1. Respond to comments quickly and technically.
2. Be honest about the current boundary: SDK first, dashboard later.
3. If someone asks about competitors, focus on runtime enforcement and coding-agent safety.
4. If someone asks how to try it, point them to `doctor`, `demo`, and `demo_budget_kill.py`.
5. Capture every useful objection as future onboarding work.

## Alternate Titles

- `Show HN: I built a kill switch for coding agents`
- `Show HN: Zero-dependency Python guardrails for coding agents`
- `Show HN: Stop coding agents from looping, retrying forever, and burning budget`
