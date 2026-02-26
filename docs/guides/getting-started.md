# Getting Started with AgentGuard

Get from zero to your first traced agent run in under 5 minutes.

## Install

```bash
pip install agentguard47
```

Zero dependencies. Python 3.9+.

## 1. Trace an agent run

```python
from agentguard import Tracer, JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search for docs"})

    with span.span("tool.search", data={"query": "python asyncio"}) as tool:
        result = "found 3 results"  # your tool call here
        tool.event("tool.result", data={"result": result})

    span.event("reasoning.step", data={"thought": "summarize results"})
```

This writes every step to `traces.jsonl` — reasoning, tool calls, timing, everything.

## 2. View the trace

```bash
agentguard report traces.jsonl
```

```
AgentGuard report
  Total events: 6
  Spans: 2  Events: 4
  Approx run time: 0.3 ms
```

## 3. Add a loop guard

Stop agents that repeat themselves. Guards auto-check on every `span.event()` call:

```python
from agentguard import Tracer, LoopGuard, LoopDetected, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[LoopGuard(max_repeats=3)],
)

with tracer.trace("agent.run") as span:
    for step in range(10):
        try:
            # LoopGuard checks fire on event(), not on span()
            span.event("tool.call", data={"tool": "search", "query": "test"})
        except LoopDetected as e:
            print(f"Loop caught: {e}")
            break
```

## 4. Add a budget guard

Cap spend per agent run:

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)],
)

# BudgetGuard tracks token usage and estimated cost.
# Raises BudgetExceeded when the limit is hit.
# Fires BudgetWarning at 80% of the limit.
```

## 5. Auto-instrument OpenAI

Skip manual tracing — let AgentGuard patch the OpenAI client:

```python
from agentguard import Tracer, JsonlFileSink, patch_openai

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
patch_openai(tracer)

# Every OpenAI call is now traced with token counts and cost estimates.
# Works with openai>=1.0 client instances.
```

Same for Anthropic:

```python
from agentguard import patch_anthropic
patch_anthropic(tracer)
```

## 6. Use with LangChain

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

# Pass to any LangChain LLM or agent:
result = agent.invoke(
    {"input": "your question"},
    config={"callbacks": [handler]},
)
```

## 7. Send traces to the dashboard

Swap the file sink for an HTTP sink to see traces in the hosted dashboard:

```python
from agentguard import Tracer, HttpSink

sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_...",
)
tracer = Tracer(sink=sink, service="my-agent")
```

Sign up at [app.agentguard47.com](https://app.agentguard47.com) to get an API key.

## Next steps

- [Examples](https://github.com/bmdhodl/agent47/tree/main/examples) — LangChain, CrewAI, OpenAI integration examples
- [Guards reference](https://github.com/bmdhodl/agent47#guards) — LoopGuard, FuzzyLoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard
- [Evaluation](https://github.com/bmdhodl/agent47#evaluation) — assertion-based trace analysis for CI
- [Async support](https://github.com/bmdhodl/agent47#async) — AsyncTracer, async decorators
