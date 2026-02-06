# AgentGuard SDK (Python)

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/bmdhodl/agent47/blob/main/LICENSE)

Lightweight, zero-dependency observability for multi-agent AI systems. Trace reasoning steps, catch loops, guard budgets, and replay runs deterministically.

## Install

```bash
pip install agentguard47
```

With LangChain support:
```bash
pip install agentguard47[langchain]
```

## Quickstart (2 minutes)

```bash
pip install agentguard47
```

```python
from agentguard import Tracer, LoopGuard
from agentguard.tracing import JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
guard = LoopGuard(max_repeats=3)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
    guard.check(tool_name="search", tool_args={"query": "agent loops"})
    with span.span("tool.search"):
        pass  # your tool here
```

```bash
agentguard report traces.jsonl   # summary table
agentguard view traces.jsonl     # Gantt timeline in browser
```

No config, no dependencies, no account needed.

## Tracing

```python
from agentguard.tracing import Tracer

tracer = Tracer()

with tracer.trace("agent.run", data={"user_id": "u123"}) as span:
    span.event("reasoning.step", data={"step": 1, "thought": "search docs"})
    with span.span("tool.call", data={"tool": "search", "query": "agent loops"}):
        pass
```

## Guards

```python
from agentguard.guards import LoopGuard, BudgetGuard, TimeoutGuard

# Detect repeated tool calls
guard = LoopGuard(max_repeats=3)
guard.check(tool_name="search", tool_args={"query": "agent loops"})

# Track token and call budgets
budget = BudgetGuard(max_tokens=50000, max_calls=100)
budget.record_tokens(150)
budget.record_call()

# Enforce wall-clock time limits
timeout = TimeoutGuard(max_seconds=30)
timeout.start()
timeout.check()  # raises TimeoutExceeded if over limit
```

## Replay

```python
from agentguard.recording import Recorder, Replayer

recorder = Recorder("runs.jsonl")
recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

replayer = Replayer("runs.jsonl")
resp = replayer.replay_call("llm", {"prompt": "hi"})
```

## Evaluation as Code

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_tool_called("search", min_times=1)
    .assert_budget_under(tokens=50000)
    .assert_completes_within(30.0)
    .assert_no_errors()
    .run()
)
print(result.summary)
```

## Auto-Instrumentation

```python
from agentguard import Tracer
from agentguard.instrument import trace_agent, trace_tool

tracer = Tracer()

@trace_agent(tracer)
def my_agent(query):
    return search(query)

@trace_tool(tracer)
def search(q):
    return f"results for {q}"

# Monkey-patch OpenAI/Anthropic (safe if not installed)
from agentguard.instrument import patch_openai, patch_anthropic
patch_openai(tracer)
patch_anthropic(tracer)
```

## CLI

```bash
# Summarize trace events
agentguard summarize traces.jsonl

# Human-readable report
agentguard report traces.jsonl

# Open Gantt trace viewer in browser
agentguard view traces.jsonl

# Run evaluation assertions
agentguard eval traces.jsonl
```

## Trace Viewer

```bash
agentguard view traces.jsonl --port 8080
```

Gantt-style timeline with color-coded spans (reasoning, tool, LLM, guard, error), click-to-expand detail panel, and aggregate stats.

## Integrations

- LangChain: `agentguard.integrations.langchain`

## Cloud (Hosted Dashboard)

Send traces to the hosted dashboard instead of local JSONL files:

```python
from agentguard import Tracer
from agentguard.sinks.http import HttpSink

sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
tracer = Tracer(sink=sink, service="my-agent")

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
```

Get your API key at [app.agentguard47.com](https://app.agentguard47.com). Free tier: 10K events/month.

## Links

- [GitHub](https://github.com/bmdhodl/agent47)
- [Dashboard](https://app.agentguard47.com)
- [Trace Schema](https://github.com/bmdhodl/agent47/blob/main/docs/trace_schema.md)
- [Examples](https://github.com/bmdhodl/agent47/tree/main/sdk/examples)
