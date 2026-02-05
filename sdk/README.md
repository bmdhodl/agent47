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

## Quickstart

```python
from agentguard import Tracer, LoopGuard, BudgetGuard

tracer = Tracer()
loop_guard = LoopGuard(max_repeats=3)
budget_guard = BudgetGuard(max_tokens=10000)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})

    loop_guard.check(tool_name="search", tool_args={"query": "agent loops"})
    budget_guard.record_tokens(150)

    with span.span("tool.call", data={"tool": "search"}):
        pass  # call your tool here
```

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

## CLI

```bash
# Summarize trace events
agentguard summarize traces.jsonl

# Human-readable report
agentguard report traces.jsonl

# Open trace viewer in browser
agentguard view traces.jsonl
```

## Trace Viewer

```bash
agentguard view traces.jsonl --port 8080
```

## Integrations

- LangChain: `agentguard.integrations.langchain`

## Links

- [GitHub](https://github.com/bmdhodl/agent47)
- [Trace Schema](https://github.com/bmdhodl/agent47/blob/main/docs/trace_schema.md)
- [Examples](https://github.com/bmdhodl/agent47/tree/main/sdk/examples)
