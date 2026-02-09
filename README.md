# AgentGuard

**Runtime guardrails for AI agents.** Stop loops, enforce budgets, trace everything — zero dependencies.

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![Python](https://img.shields.io/pypi/pyversions/agentguard47)](https://pypi.org/project/agentguard47/)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen)](https://github.com/bmdhodl/agent47)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

```bash
pip install agentguard47
```

## Quickstart

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    guards=[LoopGuard(max_repeats=3), BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "search docs"})
    with span.span("tool.search", data={"query": "quantum computing"}):
        pass  # your tool logic
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
```

```
$ agentguard report traces.jsonl

AgentGuard report
  Total events: 9
  Spans: 6  Events: 3
  Approx run time: 0.4 ms
  Tool results: 2
  Estimated cost: $0.01
```

That's it. Your agent now has loop detection, budget enforcement, cost tracking, and structured traces — all from a single pure-Python package.

## Why AgentGuard

Multi-agent systems fail in ways normal software doesn't: infinite tool loops, silent cost blowouts, and nondeterministic regressions. Existing observability tools show you what happened *after* the damage is done. AgentGuard intervenes at runtime — stopping loops and killing runaway spending *before* they drain your API budget.

**What makes it different:**
- **Runtime intervention**, not just tracing — guards raise exceptions to stop bad behavior
- **Zero dependencies** — pure Python stdlib, no transitive supply chain risk
- **Framework-agnostic** — works with LangChain, LangGraph, CrewAI, or raw API calls
- **Production-ready** — gzip compression, retry with backoff, sampling, SSRF protection

## Guards

Guards are runtime safety checks that raise exceptions when limits are hit.

| Guard | What it catches | Key params |
|-------|----------------|------------|
| `LoopGuard` | Exact repeated tool calls | `max_repeats=3, window=6` |
| `FuzzyLoopGuard` | Same tool with varying args, A-B-A-B alternation | `max_tool_repeats=5, max_alternations=3` |
| `BudgetGuard` | Token, call, or dollar cost overruns | `max_tokens`, `max_calls`, `max_cost_usd` |
| `TimeoutGuard` | Wall-clock time limits | `max_seconds=300` |
| `RateLimitGuard` | Calls-per-minute throttling | `max_calls_per_minute=60` |

```python
from agentguard import LoopGuard, BudgetGuard, LoopDetected, BudgetExceeded

loop_guard = LoopGuard(max_repeats=3)
budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8, on_warning=print)

try:
    loop_guard.check(tool_name="search", tool_args={"q": "same query"})
    budget.consume(tokens=1000, calls=1, cost_usd=0.05)
except LoopDetected:
    print("Agent is stuck in a loop")
except BudgetExceeded:
    print("Budget limit reached")
```

## Integrations

### LangChain

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"))
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

# Pass to any LangChain component
llm = ChatOpenAI(callbacks=[handler])
```

### LangGraph

```bash
pip install agentguard47[langgraph]
```

```python
from agentguard.integrations.langgraph import guarded_node, guard_node

@guarded_node(tracer=tracer, loop_guard=LoopGuard(max_repeats=3))
def research_node(state):
    return {"messages": state["messages"] + [result]}

# Or wrap at graph construction time:
builder.add_node("research", guard_node(research_fn, tracer=tracer))
```

### CrewAI

```bash
pip install agentguard47[crewai]
```

```python
from agentguard.integrations.crewai import AgentGuardCrewHandler

handler = AgentGuardCrewHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

agent = Agent(role="researcher", step_callback=handler.step_callback)
task = Task(description="Research topic", agent=agent, callback=handler.task_callback)
```

### OpenTelemetry

```bash
pip install agentguard47[otel]
```

```python
from opentelemetry.sdk.trace import TracerProvider
from agentguard.sinks.otel import OtelTraceSink

provider = TracerProvider()
sink = OtelTraceSink(provider)
tracer = Tracer(sink=sink, service="my-agent")
```

### OpenAI / Anthropic Auto-Instrumentation

```python
from agentguard import Tracer, patch_openai, patch_anthropic

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"))

patch_openai(tracer)      # auto-traces all ChatCompletion calls
patch_anthropic(tracer)   # auto-traces all Messages calls

# Use clients normally — tracing happens automatically
```

## Cost Tracking

Built-in pricing for OpenAI, Anthropic, Google, Mistral, and Meta models.

```python
from agentguard import estimate_cost, CostTracker, update_prices

# Single call estimate
cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)

# Track across a trace
with tracer.trace("agent.run") as span:
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
    span.cost.add("gpt-4o", input_tokens=800, output_tokens=300)
    # cost is included automatically in the trace end event

# Add custom model pricing
update_prices({("openai", "gpt-5"): (0.05, 0.15)})
```

## Evaluation

Assert properties of your traces — in tests or CI.

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_tool_called("search", min_times=1)
    .assert_budget_under(tokens=50_000)
    .assert_completes_within(seconds=30)
    .assert_no_errors()
    .run()
)
print(result.summary)
```

```bash
agentguard eval traces.jsonl --ci   # exits non-zero on failure
```

## Async Support

Full async API mirrors the sync API.

```python
from agentguard import AsyncTracer, JsonlFileSink, patch_openai_async
from agentguard.instrument import async_trace_agent, async_trace_tool

tracer = AsyncTracer(sink=JsonlFileSink("traces.jsonl"))
patch_openai_async(tracer)

@async_trace_tool(tracer)
async def search(query: str) -> str:
    return await fetch_results(query)

@async_trace_agent(tracer)
async def agent(task: str) -> str:
    results = await search(task)
    return f"Answer: {results}"
```

## CLI

```bash
agentguard report traces.jsonl      # summary table
agentguard view traces.jsonl        # Gantt timeline in browser
agentguard summarize traces.jsonl   # event-level breakdown
agentguard eval traces.jsonl        # run evaluation assertions
agentguard eval traces.jsonl --ci   # CI mode (exit code on failure)
```

## Production

```python
from agentguard import Tracer, HttpSink, BudgetGuard, LoopGuard

tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key="ag_...",
        batch_size=20,
        flush_interval=10.0,
        compress=True,          # gzip
    ),
    guards=[LoopGuard(max_repeats=5), BudgetGuard(max_cost_usd=50.00)],
    metadata={"env": "prod", "git_sha": os.environ.get("GIT_SHA")},
    sampling_rate=0.1,          # 10% of traces
)
```

## Architecture

```
Your Agent Code
    │
    ▼
┌─────────────────────────────────────┐
│           Tracer / AsyncTracer       │  ← trace(), span(), event()
│  ┌───────────┐  ┌────────────────┐  │
│  │  Guards    │  │  CostTracker   │  │  ← runtime intervention
│  └───────────┘  └────────────────┘  │
└──────────┬──────────────────────────┘
           │ emit(event)
    ┌──────┼──────────┬───────────┐
    ▼      ▼          ▼           ▼
 JsonlFile  HttpSink  OtelTrace  Stdout
  Sink      (gzip,    Sink       Sink
            retry)
```

## What's in this repo

| Directory | Description | License |
|-----------|-------------|---------|
| `sdk/` | Python SDK — tracing, guards, evaluation, integrations | MIT |
| `site/` | Landing page | MIT |
| `mcp-server/` | MCP server — agents query their own traces | MIT |

> Dashboard is in a separate private repo ([agent47-dashboard](https://github.com/bmdhodl/agent47-dashboard)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, test commands, and PR guidelines.

## License

SDK is MIT licensed (BMD PAT LLC).
