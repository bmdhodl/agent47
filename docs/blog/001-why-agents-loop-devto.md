---
title: "Why Your AI Agent Loops (And How to See It)"
published: true
tags: [ai, python, agents, opensource]
description: "Multi-agent systems fail silently with tool loops. Here's how to catch them before they burn your budget."
canonical_url: https://github.com/bmdhodl/agent47/blob/main/docs/blog/001-why-agents-loop.md
---

Multi-agent systems fail in ways normal software does not. The most common failure mode? **Silent tool loops** — your agent calls the same tool with the same arguments over and over, burning tokens and returning garbage, while you see nothing in your logs.

This happens because most observability tools track latency, not reasoning. They tell you a request took 3 seconds but not *why* your agent decided to call `search("capital of Atlantis")` five times in a row.

## The problem

Here's a simplified agent loop. A ReAct-style agent gets a question it can't answer and keeps retrying the same search:

```python
def agent_loop(question):
    for step in range(10):
        thought = f"I should search for: {question}"
        result = search(question)  # always returns "no results"
        # agent doesn't realize results are unhelpful, loops again
```

With a real LLM, this burns through your token budget. With tool calls that have side effects (sending emails, writing to a database), it can be catastrophic.

## What it looks like with AgentGuard

Install:
```bash
pip install agentguard47
```

Add tracing and a loop guard:

```python
from agentguard import Tracer, LoopGuard, LoopDetected, JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
guard = LoopGuard(max_repeats=3)

def agent_loop(question):
    with tracer.trace("agent.run", data={"question": question}) as span:
        for step in range(10):
            span.event("reasoning.step", data={"thought": f"search for {question}"})

            try:
                guard.check(tool_name="search", tool_args={"query": question})
            except LoopDetected as e:
                span.event("guard.loop_detected", data={"error": str(e)})
                print(f"Loop caught: {e}")
                return

            with span.span("tool.call", data={"tool": "search"}):
                result = search(question)
```

Run the agent, then view the report:

```bash
agentguard report traces.jsonl
```

Output:
```
AgentGuard report
  Total events: 12
  Spans: 6  Events: 6
  Approx run time: 0.5 ms
  Reasoning steps: 3
  Tool results: 2
  LLM results: 0
  Loop guard triggered: 1 time(s)
```

The guard caught the loop on the third identical call. No tokens wasted. No silent failure.

Open the trace viewer to see the full event timeline in your browser:

```bash
agentguard view traces.jsonl
```

## Why this matters

Without tracing, loop failures are invisible. Your agent returns after 30 seconds and you don't know if it did useful work or burned $2 in API calls repeating itself.

AgentGuard gives you:
- **Reasoning traces** — see every step the agent took, not just the final output
- **Loop detection** — automatically catch repeated tool calls before they burn your budget
- **Budget guards** — set hard limits on tokens and API calls
- **Timeout guards** — kill runs that exceed wall-clock limits
- **Deterministic replay** — record runs and replay them for regression tests

## Try it yourself

Install AgentGuard:
```bash
pip install agentguard47
```

Quickstart (5 lines):
```python
from agentguard import Tracer, LoopGuard

tracer = Tracer()
guard = LoopGuard(max_repeats=3)
with tracer.trace("agent.run") as span:
    guard.check(tool_name="search", tool_args={"query": "test"})
```

The SDK is MIT-licensed, zero dependencies, and works with any agent framework. LangChain integration is built in:

```bash
pip install agentguard47[langchain]
```

Full docs and examples: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)
