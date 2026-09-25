# Cost Guardrails Guide

Recorded-budget checks for instrumented Python agent code. This is not an
invoice cap and it does not stop a provider call you never wrapped.

Read the [enforcement boundary](enforcement-boundary.md) first. That map is
the tested promise.

## Why this exists

Agents can loop, retry, and keep calling a model after you meant to stop.
`BudgetGuard` stores usage you record (or that a supported patch records) and
refuses the **next** instrumented request once that recorded total is already
at a cap.

It does **not**:

- reserve concurrent in-flight requests
- predict the next response's tokens or dollars
- intercept Cursor, Claude Code, or a raw SDK client you did not patch
- enforce OpenAI/Anthropic subscription quotas

## Quickstart

```bash
pip install agentguard47
```

```python
from agentguard import BudgetExceeded, BudgetGuard

budget = BudgetGuard(max_cost_usd=5.00)

budget.check()          # refuse if recorded usage is already at a cap
budget.consume(tokens=1500, calls=1, cost_usd=0.045)
```

`check()` is the preflight. `consume()` records a call that already ran.
Reproduce an exhausted budget blocking the next mocked dispatch with
`examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py`.
Two threads can both pass `check()` today; see
`examples/enforcement_boundary/two_worker_overshoot.py`.

## Configuration

### BudgetGuard Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | `int` | `None` | Recorded token cap. `None` = unlimited |
| `max_calls` | `int` | `None` | Recorded call cap. `None` = unlimited |
| `max_cost_usd` | `float` | `None` | Recorded estimated-cost cap. `None` = unlimited |
| `warn_at_pct` | `float` | `None` | Fraction (0.0-1.0) to trigger warning. `None` = no warning |
| `on_warning` | `callable` | `None` | Callback invoked with message when `warn_at_pct` is crossed |

At least one of `max_tokens`, `max_calls`, or `max_cost_usd` is required.

### Examples

```python
BudgetGuard(max_cost_usd=10.00)
BudgetGuard(max_cost_usd=5.00, max_calls=100, warn_at_pct=0.8)
BudgetGuard(max_tokens=50_000)
```

### consume() Method

```python
budget.consume(tokens=0, calls=0, cost_usd=0.0)
```

Call after each LLM API call you want counted. Raises `BudgetExceeded` if the
new recorded total exceeds a configured cap. The call you just made is not
undone.

### Checking State

```python
state = budget.state
print(f"Tokens: {state.tokens_used}")
print(f"Calls: {state.calls_used}")
print(f"Cost: ${state.cost_used:.4f}")
```

## How costs are calculated

Estimates use published per-token prices. They are not invoices. For models
not in the built-in list, use `update_prices()`. Supply reported cost or
strict cost resolution when an estimate is not enough.

```python
from agentguard import estimate_cost

cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
```

## Auto-tracking with OpenAI / Anthropic

```python
from agentguard import Tracer, BudgetGuard, patch_openai, patch_anthropic

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(service="my-agent")

patch_openai(tracer, budget_guard=budget)
patch_anthropic(tracer, budget_guard=budget)
```

These patches cover Chat Completions and Anthropic Messages, including
streamed final usage. They check recorded usage before dispatch. The OpenAI
Responses API is unsupported. A response can still exceed remaining tokens or
cost. In-memory requests do not reserve capacity. Store-backed sync OpenAI
calls and store-backed streams do. That hold is not an invoice.

## LangChain / LangGraph / CrewAI

Framework adapters are not the same as provider patches. LangChain records LLM
usage after the call (`on_llm_end`) and can refuse a tool start when the call
budget is already exhausted. LangGraph `guarded_node` charges one call at node
entry. CrewAI `AgentGuardCrewHandler` records after the step.

See the [enforcement boundary](enforcement-boundary.md) and the integration
guides.

## Optional hosted ingest

`HttpSink` can mirror traces to the private dashboard. Local guards stay
authoritative. The sink does not execute remote kill signals and does not cap
provider invoices. See the [dashboard contract](guides/dashboard-contract.md).

## CI Cost Gates

Fail CI if **recorded traces** exceed a threshold. That is an eval on files,
not a runtime reservation.

```yaml
- uses: bmdhodl/agent47/.github/actions/agentguard-eval@main
  with:
    trace-file: traces.jsonl
    assertions: "no_errors,max_cost:5.00"
```

## FAQ

**Q: Does BudgetGuard work without a dashboard?**
Yes. It is in-process and makes no network calls by itself.

**Q: How accurate are the cost estimates?**
They follow published per-token prices for listed models. They are not the
provider invoice.

**Q: What happens when BudgetExceeded is raised?**
It is a Python exception. Catch it and stop, downshift, or return a partial
result. Swallowing it and continuing unchanged defeats the stop.

**Q: Is it thread-safe?**
`consume()` and `check()` take a lock. That lock does not reserve capacity for
in-flight requests.

**Q: Can I reset the budget mid-run?**
`reset()` reopens the in-memory counters. Persisted daily keys roll over at
the UTC day boundary.

## API Reference

- [`BudgetGuard`](https://github.com/bmdhodl/agent47/blob/main/sdk/agentguard/guards.py)
- [Enforcement boundary](enforcement-boundary.md)
- [`patch_openai()`](../README.md#connect-a-provider)
