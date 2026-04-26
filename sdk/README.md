# AgentGuard SDK (Python)

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/bmdhodl/agent47/blob/main/LICENSE)

**Zero-dependency runtime control for production Python agents.** Catch loops,
cap retries, enforce budgets, and keep the first run local and deterministic.
Add the hosted dashboard later when you need retained incidents, alerts, team
visibility, or dashboard-driven remote kill signals.

## Install

```bash
pip install agentguard47
```

## Verify the local path

```bash
agentguard doctor
agentguard demo
```

`doctor` validates the SDK in local-only mode, writes a small JSONL trace, and
prints the smallest correct next-step snippet for the current environment.
`demo` proves budget, loop, and retry protection without API keys or network
calls.

## Generate a framework starter

```bash
agentguard quickstart --framework raw
agentguard quickstart --framework openai
agentguard quickstart --framework langchain --json
```

Use this when you already know the stack you want to wire. It prints the
install command, a minimal starter file, and the next verification commands.

## Optional repo-local defaults

Use `.agentguard.json` when you want a repo-local, auditable config that both
humans and coding agents can share:

```json
{
  "profile": "coding-agent",
  "service": "support-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

`agentguard.init()` and `agentguard doctor` read this automatically. Keep it
strictly local: no secrets, no API keys, no hosted dashboard settings.

For coding-agent onboarding, prefer `agentguard.init(local_only=True)` while
you validate the local path. The checked-in starter files live in the repo
under `examples/starters/`; they are not part of the installed wheel.

For agent-specific setup snippets, see
`docs/guides/coding-agent-safety-pack.md` in the main repo.

## MCP Server

If your coding agent already uses MCP, the repo also ships a published MCP
server:

```bash
npx -y @agentguard47/mcp-server
```

That server is for querying retained traces and alerts later. The SDK remains
the local-first runtime enforcement layer.

## Quickstart

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink

sink = JsonlFileSink(".agentguard/traces.jsonl")
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
agentguard report .agentguard/traces.jsonl      # summary table
agentguard incident .agentguard/traces.jsonl    # incident-style local report
```

`agentguard report` now includes a local savings ledger with exact and
estimated token and dollar savings when the trace contains enough evidence.

The intended user journey is:
- `pip install agentguard47`
- `agentguard doctor`
- `agentguard demo`
- `agentguard quickstart --framework <stack>`
- wire the real coding agent only after the local path is proven

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

`HttpSink` sends trace and decision events to the hosted dashboard. It does not
poll or execute remote kill signals by itself; local guards remain the
authoritative runtime stop path.

Hosted contract guide:
`docs/guides/dashboard-contract.md` in the main repo.

## CLI

```bash
agentguard doctor                                 # local install verification
agentguard quickstart --framework openai          # framework-specific starter
python examples/starters/agentguard_raw_quickstart.py
agentguard demo                                   # offline proof of guardrails
agentguard report .agentguard/traces.jsonl        # human-readable summary
agentguard incident .agentguard/traces.jsonl      # postmortem-style local report
agentguard summarize .agentguard/traces.jsonl     # event-level breakdown
agentguard eval .agentguard/traces.jsonl          # run evaluation assertions
agentguard eval .agentguard/traces.jsonl --ci     # CI mode (stricter checks, exit code)
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
- [MCP Server](https://github.com/bmdhodl/agent47/tree/main/mcp-server)
- [Examples](https://github.com/bmdhodl/agent47/tree/main/examples)
