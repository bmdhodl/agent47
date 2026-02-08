# Outreach Templates

> **These templates are now auto-generated** by the scout workflow using
> `scripts/update_scout_context.py` → `docs/outreach/scout_context.json`.
>
> Edit the feature list and code snippets in `scripts/update_scout_context.py`,
> then the daily scout issue will include ready-to-paste comments with current
> version numbers, features, and code examples.
>
> The templates below are kept as a quick manual reference.

## Template 1: Reply to "my agent keeps looping"

I built an open-source guard for exactly this — detects repeated tool calls and kills the run before it burns your budget.

```python
from agentguard import LoopGuard

guard = LoopGuard(max_repeats=3)
guard.check(tool_name="search", tool_args={"query": "..."})
# raises LoopDetected after 3 identical calls
```

Works with LangChain too:

```python
from agentguard.integrations.langchain import AgentGuardCallbackHandler
from agentguard import LoopGuard, BudgetGuard

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)
llm = ChatOpenAI(callbacks=[handler])  # auto-tracks cost per call
```

Zero dependencies. `pip install agentguard47`

https://github.com/bmdhodl/agent47

Happy to help debug your specific loop if you share more details.

## Template 2: Reply to "agent cost is out of control"

Had the same problem. Built a budget guard that kills runs at a dollar threshold:

```python
from agentguard import BudgetGuard

guard = BudgetGuard(max_cost_usd=5.00)  # stop at $5
guard.consume(cost_usd=0.12)  # track per-call cost
# raises BudgetExceeded when over budget
```

Also auto-estimates cost per LLM call (OpenAI, Anthropic, Gemini, Mistral) so you can see exactly how much each agent run costs. Zero deps: `pip install agentguard47`

https://github.com/bmdhodl/agent47

## Template 3: Reply to "how do I debug my agent"

I built AgentGuard for this — it traces every reasoning step and tool call, then gives you a report + Gantt timeline in your browser:

```bash
agentguard report traces.jsonl   # summary table with cost
agentguard view traces.jsonl     # Gantt timeline in browser
```

Also has dollar cost per call, loop detection, and budget guards. Works with LangChain or any custom agent. `pip install agentguard47`

https://github.com/bmdhodl/agent47

## Template 4: Short share post (Discord / Reddit / X)

I built a tiny Python SDK that catches AI agent failures before they burn your budget.

- Cost tracking: dollar estimates per LLM call (OpenAI, Anthropic, Gemini, Mistral)
- Budget guards: `BudgetGuard(max_cost_usd=5.00)` stops agents before they blow your API budget
- Loop detection: catches repeated tool calls in a sliding window
- LangChain integration: drop-in callback handler with auto cost + guard wiring
- Gantt trace viewer: timeline visualization in your browser
- Zero dependencies: pure Python stdlib, nothing to audit

`pip install agentguard47`

https://github.com/bmdhodl/agent47

Would love feedback from anyone building agents.
