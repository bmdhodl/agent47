# Outreach Templates (copy-paste ready)

## Template 1: Reply to "my agent keeps looping"
---
I built a small open-source tool for exactly this. It's a loop guard you drop into your agent code — detects repeated tool calls and kills the run before it burns your budget.

```python
from agentguard import LoopGuard, LoopDetected

guard = LoopGuard(max_repeats=3)

# call this before each tool invocation
guard.check(tool_name="search", tool_args={"query": "..."})
# raises LoopDetected after 3 identical calls
```

Zero dependencies, works with any framework. `pip install agentguard47`

Repo: https://github.com/bmdhodl/agent47

Happy to help debug your specific loop if you share more details.

---

## Template 2: Reply to "agent cost is out of control"
---
Had the same problem. Built a budget guard that kills runs when they exceed token or call limits:

```python
from agentguard import BudgetGuard

guard = BudgetGuard(max_tokens=50000, max_calls=100)
guard.consume(tokens=150)  # track usage
guard.consume(calls=1)     # raises BudgetExceeded when over
```

Also has loop detection to catch the #1 cause of cost blowups (agent repeating the same tool call). Zero deps: `pip install agentguard47`

https://github.com/bmdhodl/agent47

---

## Template 3: Reply to "how do I debug my agent"
---
I built AgentGuard for this — it traces every reasoning step, tool call, and decision your agent makes, then gives you a human-readable report:

```
agentguard report traces.jsonl

Total events: 21
Reasoning steps: 6
Tool results: 3
Loop guard triggered: 3 time(s)
```

Also has a browser-based trace viewer. Works with LangChain or any custom agent. `pip install agentguard47`

https://github.com/bmdhodl/agent47

---

## Template 4: Short share post (Discord / Reddit / X)
---
I built a tiny Python SDK that catches AI agent failures before they burn your budget.

- Loop detection (catches repeated tool calls)
- Budget + timeout guards
- Trace viewer in your browser
- Works with LangChain or any framework
- Zero dependencies

`pip install agentguard47`

https://github.com/bmdhodl/agent47

Would love feedback from anyone building agents.

---

## Template 5: GitHub Issue comment (on langchain/crewai loop issues)
---
Hey, I built an open-source guard specifically for this pattern. It detects repeated tool calls in a sliding window and raises an exception before the loop continues:

```python
from agentguard import LoopGuard

guard = LoopGuard(max_repeats=3, window=6)
guard.check(tool_name="search", tool_args={"query": "x"})
```

There's also a LangChain callback handler that wires this in automatically:

```python
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_tokens=50000),
)
llm = ChatOpenAI(callbacks=[handler])
```

`pip install agentguard47[langchain]`

https://github.com/bmdhodl/agent47
