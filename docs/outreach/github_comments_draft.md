# GitHub Issue Comments — AgentGuard Draft Responses

Draft comments for developers experiencing agent loop/cost issues. Uses the REAL agentguard47 API.

---

## google/adk-python #4179 — FunctionCallingConfig(mode='ANY') causes infinite tool-calling loop when sub-agent is used as a tool
URL: https://github.com/google/adk-python/issues/4179
Posted: Feb 5, 2026

### Draft Comment:

I ran into this exact pattern when building multi-agent systems with forced tool calling. The `mode='ANY'` guarantees a tool call on every turn, but without a termination condition the agent just keeps calling the same tool forever.

I built a small open-source guard for exactly this. It tracks tool call patterns in a sliding window and raises an exception when it detects a loop:

```python
from agentguard import LoopGuard, LoopDetected

guard = LoopGuard(max_repeats=3, window=6)

# Call this before each tool invocation in your agent loop
try:
    guard.check(tool_name="external_search_tool", tool_args={"query": query})
    result = external_search_tool(query)
except LoopDetected:
    # Agent called the same tool with same args 3x in a row — break out
    result = "Loop detected, returning last known good result"
```

Zero dependencies, works with any framework. `pip install agentguard47`

Repo: https://github.com/bmdhodl/agent47

Happy to help debug your specific sub-agent setup if you want to share more details.

---

## DayuanJiang/next-ai-draw-io #455 — [Important] Infinite Tool-Call Loop Drained $10 in 30 Minutes (Recursive Retry Issue)
URL: https://github.com/DayuanJiang/next-ai-draw-io/issues/455
Posted: Dec 30, 2025

### Draft Comment:

That's brutal — 3,728 requests in 31 minutes with no circuit breaker. This is the exact failure mode I keep seeing across agent frameworks.

I built a guard specifically for this after a similar incident. It combines loop detection (catches repeated tool calls) with a hard budget limit:

```python
from agentguard import LoopGuard, BudgetGuard, LoopDetected, BudgetExceeded

loop_guard = LoopGuard(max_repeats=3)    # kill after 3 identical calls
budget_guard = BudgetGuard(max_calls=50)  # hard cap at 50 tool invocations

# In your agent loop, before each tool call:
try:
    loop_guard.check(tool_name="display_diagram", tool_args={"input": user_input})
    budget_guard.consume(calls=1)
    # ... run the tool
except LoopDetected:
    print("Agent stuck in a loop — stopping")
except BudgetExceeded:
    print("Too many calls — stopping")
```

For your `display_diagram` case, the LoopGuard would catch the repeated calls after 3 iterations instead of letting it run 3,728 times.

Zero dependencies, MIT licensed: `pip install agentguard47`

Repo: https://github.com/bmdhodl/agent47

---

## langchain-ai/langchain #34884 — Dynamically ends Agent loop in Tool execution
URL: https://github.com/langchain-ai/langchain/issues/34884
Posted: Jan 31, 2026

### Draft Comment:

I needed the same thing — a way for tools to signal "I'm done, stop the agent loop."

The pattern I use is a LoopGuard that sits outside the agent loop and watches for completion conditions. For LangChain specifically, there's a callback handler that wires this in automatically:

```python
from agentguard import LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_tokens=50000),
)

# The handler auto-traces all chain/tool/LLM calls
# and raises LoopDetected if a tool is called 3x with the same args
llm = ChatOpenAI(callbacks=[handler])
```

For the "tool decides the task is complete" use case, you can raise a custom exception from your tool and catch it at the agent level — the handler will log it as a clean exit rather than an error.

`pip install agentguard47[langchain]`

Repo: https://github.com/bmdhodl/agent47

Not a native LangChain solution, but might be useful until there's built-in support. Happy to discuss the approach.

---

## crewAIInc/crewAI #4246 — [Enhancement] Add debug logging when OutputParserError triggers agent retry
URL: https://github.com/crewAIInc/crewAI/issues/4246
Posted: Feb 4, 2026

### Draft Comment:

+1 on this. The silent retry problem is painful — you burn tokens and time with zero visibility into what went wrong.

I built a tracing SDK that captures every step of an agent run, which helps a lot with diagnosing retry loops:

```python
from agentguard import Tracer, LoopGuard
from agentguard.tracing import JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("crew_trace.jsonl"))
loop_guard = LoopGuard(max_repeats=3)

with tracer.trace("crew.task") as span:
    span.event("reasoning.step", data={"thought": "planning research"})

    # Before each tool/LLM call, check for loops
    loop_guard.check(tool_name="llm_call", tool_args={"prompt": prompt})

    with span.span("llm.call", data={"model": "gpt-4", "prompt": prompt}):
        response = llm.call(prompt)

    span.event("llm.result", data={"response": response, "tokens": token_count})
```

Then inspect with: `agentguard report crew_trace.jsonl`

```
AgentGuard report
  Total events: 14
  Reasoning steps: 3
  Tool results: 2
  Loop guard triggered: 1 time(s)
```

It won't solve the CrewAI-native logging gap, but it gives you full visibility into what's happening during retries right now. Zero deps: `pip install agentguard47`

https://github.com/bmdhodl/agent47

---

## adenhq/hive #3678 — Integration: FinOps / Cost Guardrails — OpenTelemetry + Prometheus Exporter
URL: https://github.com/adenhq/hive/issues/3678
Posted: Feb 5, 2026

### Draft Comment:

Really well-thought-out spec. The `runaway_loop_suspected` metric is something I've been tracking in my own agent deployments.

I built an open-source SDK that covers a chunk of what you're describing — specifically the runtime loop detection, budget enforcement, and per-run tracing:

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, TimeoutGuard
from agentguard.tracing import JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("agent_traces.jsonl"))
loop_guard = LoopGuard(max_repeats=3, window=6)
budget_guard = BudgetGuard(max_tokens=100000, max_calls=200)
timeout_guard = TimeoutGuard(max_seconds=60)

timeout_guard.start()

with tracer.trace("agent.run") as span:
    # Each tool call gets traced + guarded
    loop_guard.check(tool_name="search", tool_args={"query": q})
    budget_guard.consume(tokens=150, calls=1)
    timeout_guard.check()

    with span.span("tool.search", data={"query": q}):
        result = search(q)
```

The traces export as JSONL (one event per line), which is easy to pipe into whatever metrics stack you're using. Each event includes trace_id, span_id, timing, token counts, and error data.

What it covers from your spec:
- `tokens_in/tokens_out` per tool — via BudgetGuard tracking
- `runaway_loop_suspected` — via LoopGuard (detects repeated tool calls in a sliding window)
- `budget_policy_triggered` — BudgetGuard raises BudgetExceeded when limits hit
- Wall-clock timeout — TimeoutGuard

What it doesn't cover yet: native OTel export, Prometheus scraping, `cost_per_successful_outcome`. The JSONL sink is the current export path.

`pip install agentguard47` — https://github.com/bmdhodl/agent47

Would be interested in collaborating on a Hive integration if you're open to it. The architecture here is solid and the guard primitives could plug in pretty naturally.
