# AgentGuard

**Your AI agent just burned $200 in one run. AgentGuard would have stopped it at $5.**

Set a dollar budget. Get warnings at 80%. Kill the agent when it exceeds the limit. Zero dependencies, works with any framework.

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![Downloads](https://img.shields.io/pypi/dm/agentguard47)](https://pypi.org/project/agentguard47/)
[![Python](https://img.shields.io/pypi/pyversions/agentguard47)](https://pypi.org/project/agentguard47/)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/bmdhodl/agent47)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/bmdhodl/agent47/badge)](https://scorecard.dev/viewer/?uri=github.com/bmdhodl/agent47)
[![GitHub stars](https://img.shields.io/github/stars/bmdhodl/agent47?style=social)](https://github.com/bmdhodl/agent47)

```bash
pip install agentguard47
```

<!-- Replace with recorded GIF: vhs examples/demo.tape -->
![AgentGuard BudgetGuard Demo](examples/demo.gif)

## Try it in 60 seconds

No API keys. No config. Just run it:

```bash
pip install agentguard47 && python examples/try_it_now.py
```

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdhodl/agent47/blob/main/examples/quickstart.ipynb)

## Quickstart: Stop Runaway Costs in 4 Lines

```python
from agentguard import Tracer, BudgetGuard, patch_openai

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)])
patch_openai(tracer)  # auto-tracks every OpenAI call

# Use OpenAI normally — AgentGuard tracks cost and kills the agent at $5
```

That's it. Every `ChatCompletion` call is tracked. When accumulated cost hits $4 (80%), your warning fires. At $5, `BudgetExceeded` is raised and the agent stops.

No config files. No dashboard required. No dependencies.

## The Problem

AI agents are expensive and unpredictable:
- **Cost overruns average 340%** on autonomous agent tasks ([source](https://arxiv.org/abs/2401.15811))
- A single stuck loop can burn through your entire OpenAI budget in minutes
- Existing tools (LangSmith, Langfuse, Portkey) show you the damage *after* it happens

**AgentGuard is the only tool that kills agents mid-run when they exceed spend limits.**

| | AgentGuard | LangSmith | Langfuse | Portkey |
|---|---|---|---|---|
| Hard budget enforcement | **Yes** | No | No | No |
| Kill agent mid-run | **Yes** | No | No | No |
| Loop detection | **Yes** | No | No | No |
| Cost tracking | **Yes** | Yes | Yes | Yes |
| Zero dependencies | **Yes** | No | No | No |
| Self-hosted option | **Yes** | No | Yes | No |
| Price | **Free (MIT)** | $2.50/1k traces | $59/mo | $49/mo |

## Guards

Guards are runtime checks that raise exceptions when limits are hit. The agent stops immediately.

| Guard | What it stops | Example |
|-------|--------------|---------|
| `BudgetGuard` | Dollar/token/call overruns | `BudgetGuard(max_cost_usd=5.00)` |
| `LoopGuard` | Exact repeated tool calls | `LoopGuard(max_repeats=3)` |
| `FuzzyLoopGuard` | Similar tool calls, A-B-A-B patterns | `FuzzyLoopGuard(max_tool_repeats=5)` |
| `TimeoutGuard` | Wall-clock time limits | `TimeoutGuard(max_seconds=300)` |
| `RateLimitGuard` | Calls-per-minute throttling | `RateLimitGuard(max_calls_per_minute=60)` |

```python
from agentguard import BudgetGuard, BudgetExceeded

budget = BudgetGuard(
    max_cost_usd=10.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"WARNING: {msg}"),
)

# In your agent loop:
budget.consume(tokens=1500, calls=1, cost_usd=0.03)
# At 80% → warning callback fires
# At 100% → BudgetExceeded raised, agent stops
```

## Integrations

### LangChain

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import Tracer, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00)])
handler = AgentGuardCallbackHandler(
    tracer=tracer,
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
from agentguard.integrations.langgraph import guarded_node

@guarded_node(tracer=tracer, budget_guard=BudgetGuard(max_cost_usd=5.00))
def research_node(state):
    return {"messages": state["messages"] + [result]}
```

### CrewAI

```bash
pip install agentguard47[crewai]
```

```python
from agentguard.integrations.crewai import AgentGuardCrewHandler

handler = AgentGuardCrewHandler(
    tracer=tracer,
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

agent = Agent(role="researcher", step_callback=handler.step_callback)
```

### OpenAI / Anthropic Auto-Instrumentation

```python
from agentguard import Tracer, BudgetGuard, patch_openai, patch_anthropic

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00)])
patch_openai(tracer)      # auto-tracks all ChatCompletion calls
patch_anthropic(tracer)   # auto-tracks all Messages calls
```

## Cost Tracking

Built-in pricing for OpenAI, Anthropic, Google, Mistral, and Meta models. Updated monthly.

```python
from agentguard import estimate_cost, CostTracker, update_prices

# Single call estimate
cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
# → $0.00625

# Track across a trace
with tracer.trace("agent.run") as span:
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
    span.cost.add("claude-sonnet-4-5-20250929", input_tokens=800, output_tokens=300)
    # cost_usd included in trace end event

# Add custom model pricing (input $/1M, output $/1M)
update_prices({("openai", "gpt-5"): (0.05, 0.15)})
```

## Tracing

Full structured tracing with zero dependencies — JSONL output, spans, events, and cost data.

```python
from agentguard import Tracer, JsonlFileSink, BudgetGuard

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    guards=[BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "search docs"})
    with span.span("tool.search", data={"query": "quantum computing"}):
        pass  # your tool logic
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
```

```bash
$ agentguard report traces.jsonl

AgentGuard report
  Total events: 9
  Spans: 6  Events: 3
  Estimated cost: $0.01
```

## Evaluation

Assert properties of your traces in tests or CI.

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_budget_under(tokens=50_000)
    .assert_completes_within(seconds=30)
    .assert_no_errors()
    .run()
)
```

```bash
agentguard eval traces.jsonl --ci   # exits non-zero on failure
```

## CI Cost Gates

Fail your CI pipeline if an agent run exceeds a cost budget. No competitor offers this.

```yaml
# .github/workflows/cost-gate.yml (simplified)
- name: Run agent with budget guard
  run: |
    python3 -c "
    from agentguard import Tracer, BudgetGuard, JsonlFileSink
    tracer = Tracer(
        sink=JsonlFileSink('ci_traces.jsonl'),
        guards=[BudgetGuard(max_cost_usd=5.00)],
    )
    # ... your agent run here ...
    "

- name: Evaluate traces
  uses: bmdhodl/agent47/.github/actions/agentguard-eval@main
  with:
    trace-file: ci_traces.jsonl
    assertions: "no_errors,max_cost:5.00"
```

Full workflow: [`docs/ci/cost-gate-workflow.yml`](docs/ci/cost-gate-workflow.yml)

## Async Support

Full async API mirrors the sync API.

```python
from agentguard import AsyncTracer, BudgetGuard, patch_openai_async

tracer = AsyncTracer(guards=[BudgetGuard(max_cost_usd=5.00)])
patch_openai_async(tracer)

# All async OpenAI calls are now tracked and budget-enforced
```

## Production: Dashboard + Kill Switch

For teams that need centralized monitoring, alerts, and remote kill switch:

```python
from agentguard import Tracer, HttpSink, BudgetGuard

tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key="ag_...",
        batch_size=20,
        flush_interval=10.0,
        compress=True,
    ),
    guards=[BudgetGuard(max_cost_usd=50.00)],
    metadata={"env": "prod"},
    sampling_rate=0.1,  # 10% of traces
)
```

| | Free | Pro ($39/mo) | Team ($79/mo) |
|---|---|---|---|
| SDK + local guards | Unlimited | Unlimited | Unlimited |
| Dashboard traces | - | 100K/mo | 500K/mo |
| Budget alerts (email/webhook) | - | Yes | Yes |
| Remote kill switch | - | Yes | Yes |
| Team members | - | 1 | 10 |

[Start free](https://app.agentguard47.com) | [View pricing](https://agentguard47.com/#pricing)

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
| `sdk/` | Python SDK — guards, tracing, evaluation, integrations | MIT |
| `mcp-server/` | MCP server — agents query their own traces | MIT |
| `site/` | Landing page | MIT |

> Dashboard is in a separate private repo ([agent47-dashboard](https://github.com/bmdhodl/agent47-dashboard)).

## Security

- **Zero runtime dependencies** — one package, nothing to audit, no supply chain risk
- **[OpenSSF Scorecard](https://scorecard.dev/viewer/?uri=github.com/bmdhodl/agent47)** — automated security analysis on every push
- **CodeQL scanning** — GitHub's semantic code analysis on every PR
- **Bandit security linting** — Python-specific security checks in CI

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, test commands, and PR guidelines.

## License

MIT (BMD PAT LLC)
