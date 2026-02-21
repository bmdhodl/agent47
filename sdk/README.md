# AgentGuard SDK (Python)

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/bmdhodl/agent47/blob/main/LICENSE)

**Zero-dependency** observability and runtime guards for AI agents. Pure Python stdlib — nothing to audit, nothing that can break. Trace reasoning steps, catch loops, enforce budgets, and replay runs deterministically.

## Install

```bash
pip install agentguard47
```

## Quickstart

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink

sink = JsonlFileSink("traces.jsonl")
tracer = Tracer(
    sink=sink,
    service="my-agent",
    guards=[LoopGuard(max_repeats=3), BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search docs"})
    with span.span("tool.search"):
        pass  # your tool here
```

```bash
agentguard report traces.jsonl   # summary table
```

## Guards

```python
from agentguard import LoopGuard, BudgetGuard, TimeoutGuard, FuzzyLoopGuard, RateLimitGuard

# Exact loop detection
guard = LoopGuard(max_repeats=3)
guard.check(tool_name="search", tool_args={"query": "agent loops"})

# Fuzzy loop detection (same tool, different args + A-B-A-B patterns)
fuzzy = FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3)
fuzzy.check("search", {"q": "docs"})

# Budget enforcement with warning callback
budget = BudgetGuard(
    max_cost_usd=5.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"WARNING: {msg}"),
)
budget.consume(tokens=150, calls=1, cost_usd=0.02)

# Wall-clock timeout
timeout = TimeoutGuard(max_seconds=30)
timeout.start()
timeout.check()

# Rate limiting
rate = RateLimitGuard(max_calls_per_minute=60)
rate.check()
```

## Auto-Instrumentation

```python
from agentguard import Tracer, patch_openai, patch_anthropic
from agentguard import trace_agent, trace_tool

tracer = Tracer()

@trace_agent(tracer)
def my_agent(query):
    return search(query)

@trace_tool(tracer)
def search(q):
    return f"results for {q}"

# Monkey-patch OpenAI/Anthropic (safe if not installed)
patch_openai(tracer)
patch_anthropic(tracer)
```

## Async Support

```python
from agentguard import AsyncTracer, JsonlFileSink
from agentguard import async_trace_agent, async_trace_tool, patch_openai_async

tracer = AsyncTracer(sink=JsonlFileSink("traces.jsonl"), service="my-agent")
patch_openai_async(tracer)

@async_trace_agent(tracer)
async def my_agent(query: str) -> str:
    return await search(query)

@async_trace_tool(tracer)
async def search(q: str) -> str:
    return f"results for {q}"
```

## Evaluation as Code

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_tool_called("search", min_times=1)
    .assert_budget_under(tokens=50000)
    .assert_cost_under(max_cost_usd=1.00)
    .assert_completes_within(30.0)
    .assert_no_errors()
    .assert_no_budget_warnings()
    .run()
)
print(result.summary)
```

## Replay

```python
from agentguard import Recorder, Replayer

recorder = Recorder("runs.jsonl")
recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

replayer = Replayer("runs.jsonl")
resp = replayer.replay_call("llm", {"prompt": "hi"})
```

## Production Features

```python
# Metadata attached to every event
tracer = Tracer(
    sink=sink,
    metadata={"env": "production", "git_sha": "abc123"},
)

# Probabilistic sampling (emit 10% of traces)
tracer = Tracer(sink=sink, sampling_rate=0.1)

# HttpSink with gzip, retry, idempotency
from agentguard import HttpSink
sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_...",
    compress=True,
    max_retries=3,
)
```

## CLI

```bash
agentguard report traces.jsonl      # human-readable summary
agentguard summarize traces.jsonl   # event-level breakdown
agentguard eval traces.jsonl        # run evaluation assertions
agentguard eval traces.jsonl --ci   # CI mode (stricter checks, exit code)
```

## Export

```python
from agentguard.export import export_json, export_csv

export_json("traces.jsonl", "traces.json")
export_csv("traces.jsonl", "traces.csv")
```

## Benchmark

```bash
python -m agentguard.bench
```

## Migration Guide (v0.5 → v1.0)

| v0.5 | v1.0 |
|------|------|
| `from agentguard.tracing import JsonlFileSink` | `from agentguard import JsonlFileSink` |
| `from agentguard.instrument import trace_agent` | `from agentguard import trace_agent` |
| `from agentguard.instrument import patch_openai` | `from agentguard import patch_openai` |
| `budget.record_tokens(150)` | `budget.consume(tokens=150)` |
| (no async support) | `AsyncTracer`, `async_trace_agent`, `patch_openai_async` |
| (no fuzzy loops) | `FuzzyLoopGuard`, `RateLimitGuard` |
| (no budget warnings) | `BudgetGuard(warn_at_pct=0.8, on_warning=...)` |
| (no sampling) | `Tracer(sampling_rate=0.1)` |
| (no metadata) | `Tracer(metadata={"env": "prod"})` |
| (no gzip) | `HttpSink(compress=True)` |

## Links

- [GitHub](https://github.com/bmdhodl/agent47)
- [Dashboard](https://app.agentguard47.com)
- [Examples](https://github.com/bmdhodl/agent47/tree/main/sdk/examples)
