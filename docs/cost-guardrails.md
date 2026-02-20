# Cost Guardrails Guide

Stop runaway AI agent costs before they happen. This guide covers everything you need to enforce dollar budgets on agent runs.

## Why Cost Guardrails?

AI agents are expensive and unpredictable. A single agent run can make 3 or 300 LLM calls depending on the task. Without guardrails:

- A stuck agent burns your entire OpenAI budget in minutes
- Cost overruns on autonomous tasks average 340% ([source](https://arxiv.org/abs/2401.15811))
- You only find out when the invoice arrives

AgentGuard's `BudgetGuard` enforces hard dollar limits at runtime — the agent stops the moment it exceeds your budget.

## Quickstart

```bash
pip install agentguard47
```

```python
from agentguard import BudgetGuard, BudgetExceeded

budget = BudgetGuard(max_cost_usd=5.00)

# After each LLM call:
budget.consume(tokens=1500, calls=1, cost_usd=0.045)

# When cumulative cost exceeds $5.00 → BudgetExceeded raised
```

That's it. Three lines to add a hard budget to any agent.

## Configuration

### BudgetGuard Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | `int` | `None` | Maximum total tokens. `None` = unlimited |
| `max_calls` | `int` | `None` | Maximum total API calls. `None` = unlimited |
| `max_cost_usd` | `float` | `None` | Maximum total cost in USD. `None` = unlimited |
| `warn_at_pct` | `float` | `None` | Fraction (0.0-1.0) to trigger warning. `None` = no warning |
| `on_warning` | `callable` | `None` | Callback invoked with message when `warn_at_pct` is crossed |

### Examples

```python
# Dollar limit only
BudgetGuard(max_cost_usd=10.00)

# Dollar + call limit with warning
BudgetGuard(max_cost_usd=5.00, max_calls=100, warn_at_pct=0.8)

# Token limit only
BudgetGuard(max_tokens=50_000)

# Full config with warning callback
BudgetGuard(
    max_cost_usd=5.00,
    max_calls=200,
    max_tokens=100_000,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"WARNING: {msg}"),
)
```

### consume() Method

```python
budget.consume(tokens=0, calls=0, cost_usd=0.0)
```

Call after each LLM API call. Pass any combination of tokens, calls, and cost. Raises `BudgetExceeded` if any configured limit is exceeded.

### Checking State

```python
state = budget.state
print(f"Tokens: {state.tokens_used}")
print(f"Calls: {state.calls_used}")
print(f"Cost: ${state.cost_used:.4f}")
```

## How Costs Are Calculated

### Built-in Pricing

AgentGuard includes hardcoded pricing for major models (last updated 2026-02-01):

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo, o1, o1-mini, o3-mini |
| Anthropic | claude-3.5-sonnet, claude-3.5-haiku, claude-3-opus, claude-sonnet-4.5, claude-haiku-4.5, claude-opus-4.6 |
| Google | gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash |
| Mistral | mistral-large, mistral-small |
| Meta | llama-3.1-70b |

### Manual Cost Estimation

```python
from agentguard import estimate_cost

cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
# → $0.0075
```

### Custom Model Pricing

Add pricing for custom or fine-tuned models:

```python
from agentguard.cost import update_prices

# (input_price_per_1k, output_price_per_1k)
update_prices({("openai", "my-fine-tuned-model"): (0.003, 0.006)})
```

## Auto-Tracking with OpenAI / Anthropic

Skip manual `consume()` calls — patch the SDK to auto-track costs:

```python
from agentguard import Tracer, BudgetGuard, patch_openai, patch_anthropic

tracer = Tracer(
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)],
)

patch_openai(tracer)      # auto-tracks all ChatCompletion calls
patch_anthropic(tracer)   # auto-tracks all Messages calls

# Use OpenAI/Anthropic normally — costs tracked automatically
```

When done, clean up:

```python
from agentguard import unpatch_openai, unpatch_anthropic

unpatch_openai()
unpatch_anthropic()
```

## LangChain Integration

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import Tracer, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(service="my-agent")
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

# Pass to any LangChain component
llm = ChatOpenAI(callbacks=[handler])
```

The callback handler auto-extracts token usage from LLM responses and feeds it into BudgetGuard.

## LangGraph Integration

```bash
pip install agentguard47[langgraph]
```

```python
from agentguard import Tracer, BudgetGuard
from agentguard.integrations.langgraph import guarded_node

tracer = Tracer(service="my-graph-agent")
budget = BudgetGuard(max_cost_usd=5.00)

@guarded_node(tracer=tracer, budget_guard=budget)
def research_node(state):
    return {"messages": state["messages"] + [result]}
```

## Dashboard Integration

Send traces to the hosted dashboard for centralized monitoring:

```python
from agentguard import Tracer, BudgetGuard, HttpSink

tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key="ag_...",
    ),
    guards=[BudgetGuard(max_cost_usd=50.00)],
)
```

The dashboard provides:
- Real-time cost tracking across all agents
- Budget alerts via email and webhook
- Remote kill switch to stop agents mid-run
- Cost breakdown by agent, model, and time period

## CI Cost Gates

Fail CI if agent costs exceed a threshold:

```yaml
- uses: bmdhodl/agent47/.github/actions/agentguard-eval@main
  with:
    trace-file: traces.jsonl
    assertions: "no_errors,max_cost:5.00"
```

Full workflow: [docs/ci/cost-gate-workflow.yml](ci/cost-gate-workflow.yml)

## FAQ

**Q: Does BudgetGuard work without a dashboard?**
Yes. BudgetGuard is local — it runs in your process with zero network calls. The dashboard is optional.

**Q: How accurate are the cost estimates?**
Token-level accurate for supported models. AgentGuard uses published per-token pricing. For models not in the built-in list, use `update_prices()` to add custom pricing.

**Q: What happens when BudgetExceeded is raised?**
It's a normal Python exception. Your agent loop's try/except catches it and you decide what to do — log it, retry with a cheaper model, return a partial result, etc.

**Q: Is it thread-safe?**
Yes. BudgetGuard uses a lock internally. Safe to share across threads.

**Q: Can I reset the budget mid-run?**
Create a new `BudgetGuard` instance. There's no reset method by design — budgets should be immutable per run.

## API Reference

- [`BudgetGuard`](https://github.com/bmdhodl/agent47#guards) — budget enforcement
- [`estimate_cost()`](https://github.com/bmdhodl/agent47#cost-tracking) — per-call cost estimation
- [`patch_openai()`](https://github.com/bmdhodl/agent47#openai--anthropic-auto-instrumentation) — auto-instrumentation
- [`AgentGuardCallbackHandler`](https://github.com/bmdhodl/agent47#langchain) — LangChain integration
- [`guarded_node`](https://github.com/bmdhodl/agent47#langgraph) — LangGraph integration
