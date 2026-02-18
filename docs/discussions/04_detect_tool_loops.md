# How to Detect Tool Call Loops in AI Agents

**Category:** Show and tell
**Labels:** loop-detection, agents, python

---

AI agents get stuck in loops more often than most people realize. The pattern: agent calls a tool, gets a result it doesn't understand, and calls the same tool again with the same arguments. Repeat 50 times. Your token budget is gone.

This happens with every model — GPT-4, Claude, Gemini. It happens more often with complex tool schemas and ambiguous queries.

## Exact loops

Catch when the same `(tool_name, tool_args)` pair is called repeatedly:

```python
from agentguard import LoopGuard, LoopDetected

guard = LoopGuard(max_repeats=3, window=6)

# In your agent loop:
for step in agent_steps:
    try:
        guard.check(tool_name=step["tool"], tool_args=step["args"])
    except LoopDetected as e:
        print(f"Loop detected: {e}")
        break

    # Execute the tool call...
```

`LoopGuard` keeps a sliding window of recent calls. If the same call appears 3 times in a 6-call window, it raises `LoopDetected`.

## Fuzzy loops

Sometimes agents loop with slightly different arguments — `search("weather NYC")` then `search("NYC weather")`. Basic loop detection misses this.

`FuzzyLoopGuard` catches two additional patterns:

1. **Same tool, different args** — tool called too many times regardless of arguments
2. **A-B-A-B alternation** — two tools called in alternating pattern

```python
from agentguard import FuzzyLoopGuard

guard = FuzzyLoopGuard(
    max_tool_repeats=5,     # same tool called 5+ times
    max_alternations=3,     # A-B-A-B pattern 3+ times
    window=10,
)
```

## With LangChain

```python
from agentguard import LoopGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
)

agent_executor.invoke(
    {"input": "Research quantum computing"},
    config={"callbacks": [handler]},
)
```

The callback handler automatically feeds tool calls into the guard.

## Install

```bash
pip install agentguard47
```

Zero dependencies, MIT licensed, Python 3.9+.

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)

---

*What loop patterns have you seen in your agents? I'm collecting failure modes to improve detection — drop a comment with examples.*
