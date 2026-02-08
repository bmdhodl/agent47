# How to Detect Infinite Loops in LangChain Agents

**Category:** Show and tell
**Labels:** langchain, guides, loop-detection

---

If you've built a LangChain agent that calls tools, you've probably seen this: the agent calls the same tool with the same arguments, over and over, burning through your API budget while doing nothing useful.

LangChain has `max_iterations` to cap the total number of steps, but that doesn't distinguish between productive work and a stuck agent repeating itself. An agent doing 20 different things is fine. An agent calling `search("weather in NYC")` 20 times is broken.

## The pattern

Here's what an infinite loop looks like in agent logs:

```
> Entering new AgentExecutor chain...
Action: search
Action Input: {"query": "current weather NYC"}
Observation: ...
Action: search
Action Input: {"query": "current weather NYC"}
Observation: ...
Action: search
Action Input: {"query": "current weather NYC"}
...
```

The agent gets the same result, doesn't know what to do with it, and tries again. This can happen with any model (GPT-4, Claude, Gemini) and any tool configuration.

## Detecting loops at runtime

Instead of relying on iteration caps, you can detect the actual pattern — repeated identical tool calls — and stop execution immediately.

Here's how with AgentGuard's `LoopGuard`:

```python
from agentguard import LoopGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

# Stop if the same tool+args is called 3 times in a 6-call window
loop_guard = LoopGuard(max_repeats=3, window=6)
handler = AgentGuardCallbackHandler(loop_guard=loop_guard)

agent_executor.invoke(
    {"input": "What's the weather in NYC?"},
    config={"callbacks": [handler]},
)
```

When the agent enters a loop, `LoopGuard` raises `LoopDetected` with details about which tool and arguments triggered it. You can catch this and handle it however you want — retry with a different prompt, fall back to a simpler model, or return an error.

## How it works under the hood

`LoopGuard` maintains a sliding window of recent tool calls. Each call is a `(tool_name, hash(tool_args))` pair. If the same pair appears `max_repeats` times within the window, it's a loop.

The sliding window is important because it allows the agent to call the same tool multiple times with different arguments (productive work), while still catching the pathological case of identical repeated calls.

## Adding budget limits too

Loops are one failure mode. The other is cost blowouts — even without loops, a complex agent can run up a large bill. You can layer `BudgetGuard` on top:

```python
from agentguard import LoopGuard, BudgetGuard, Tracer, JsonlFileSink
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
loop_guard = LoopGuard(max_repeats=3, window=6)
budget_guard = BudgetGuard(max_cost_usd=5.00, max_calls=50)

handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=loop_guard,
    budget_guard=budget_guard,
)

try:
    result = agent_executor.invoke(
        {"input": "Research and summarize AI trends"},
        config={"callbacks": [handler]},
    )
except Exception as e:
    print(f"Agent stopped: {e}")
    print(f"Cost so far: ${budget_guard.state.cost_used:.4f}")
```

The callback handler automatically extracts token usage from LLM responses and feeds it into `BudgetGuard`. When the budget is exceeded, execution stops.

## What about fuzzy loops?

Sometimes agents loop with slightly different arguments — e.g., `search("weather NYC")` then `search("NYC weather")`. The basic `LoopGuard` won't catch this because the args differ.

For this, AgentGuard has `FuzzyLoopGuard` which detects repeated calls to the same tool regardless of arguments, and also catches A-B-A-B alternation patterns:

```python
from agentguard import FuzzyLoopGuard

guard = FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3, window=10)
```

## Install

```bash
pip install agentguard47[langchain]
```

The SDK is MIT licensed, zero dependencies, and works with Python 3.9+.

Repo: https://github.com/bmdhodl/agent47

---

*What loop patterns have you seen in your agents? Drop a comment — I'm collecting failure modes to improve detection.*
