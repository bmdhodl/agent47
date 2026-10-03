# AgentGuard vs Vercel AI Gateway

This compares AgentGuard's in-process Python checks with Vercel's managed AI
Gateway. Last checked: 2026-10-03.

## Why this comparison exists

Vercel AI Gateway routes requests to supported providers and records usage.
Applications can call it from local infrastructure or another cloud; they do
not need to run on Vercel. See the [official overview](https://vercel.com/docs/ai-gateway).

AgentGuard checks usage inside Python code you instrument. Its recorded-budget
preflight is not an invoice cap or automatic interception of a coding-agent
host. Read the [enforcement boundary](../enforcement-boundary.md).

## Comparison

| Axis | AgentGuard | Vercel AI Gateway |
|------|-----------|-------------------|
| **Deployment model** | In-process Python SDK. Runs in the same process as your agent. | Gateway proxy. All LLM calls route through Vercel's infrastructure. |
| **Provider coverage** | Supported OpenAI/Anthropic patches, or manual accounting for other calls. Coverage follows the enforcement boundary. | Routes requests to supported providers; system credentials and BYOK have different billing boundaries. |
| **Local-first** | Checks and JSONL can stay local; a provider call may still use the network. | The client can run locally, but Gateway requests use a managed network service. |
| **Latency overhead** | In-process checks add work; overhead is not measured here. No SDK-added proxy hop. | Calls route through the managed gateway. No latency benchmark is claimed here. |
| **Governance** | You own the audit log. JSONL traces on your filesystem. Export to your own storage. | Vercel hosts the audit log. You access it through their dashboard and API. |
| **Dependencies** | `pip install agentguard47`. Zero required runtime dependencies. Provider SDKs are optional. | Gateway access and network connectivity; application hosting on Vercel is optional. |
| **Price** | Free, MIT license. Provider charges are separate. | Check [current Gateway pricing](https://vercel.com/docs/ai-gateway/pricing). |

## Worked scenario: a Python agent with local Ollama fallback

Your Python agent calls a hosted provider for some work and a local Ollama
endpoint for other work. Direct requests to `localhost:11434` do not route
through Vercel AI Gateway. They need their own accounting path.

Gateway budgets cover system-credential spend. BYOK spend is metered separately;
it does not count toward those budgets. They are soft caps: a crossing request
can finish above the limit. See [Gateway budgets](https://vercel.com/docs/ai-gateway/observability-and-spend/budgets)
and [BYOK](https://vercel.com/docs/ai-gateway/authentication-and-byok/byok).

**AgentGuard's local-cost limit:** published 1.4.0's `patch_openai()` classifies an
OpenAI-compatible local endpoint as OpenAI. Unknown model prices use a
conservative estimate, so a dollar cap can stop a free local run and reports
can show phantom cost. A loopback URL alone does not prove a call is free.
The unpublished 1.4.1 candidate adds
[`free_local_clients=[client]`](../guides/free-local-clients.md) for exact clients
you declare free. It keeps paid-client estimates and token/call limits. On
published 1.4.0, token/call caps do not remove phantom cost from patched traces.

Use the existing manual helper for calls you know are free. This offline
example represents one completed OpenAI-compatible response. It does not run
a model or patch a client. The runnable file is
[`examples/local_cost_manual.py`](../../examples/local_cost_manual.py):

<!-- local-cost-example:start -->
```python
from agentguard import BudgetGuard, JsonlFileSink, Tracer, consume_billable

budget = BudgetGuard(max_tokens=3000, max_calls=1)
tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"))

budget.check()  # before the request you own
response = {
    "model": "qwen3.5:4b",
    "usage": {"prompt_tokens": 2000, "completion_tokens": 500, "total_tokens": 2500},
}
with tracer.trace("local.call") as span:
    resolved = consume_billable(
        budget, response, model=response["model"], provider="ollama", free_local=True,
    )
    span.event("llm.result", data=resolved["consume_log"], cost_usd=resolved["cost_usd"])
assert budget.state.tokens_used == 2500
assert budget.state.cost_used == 0
```
<!-- local-cost-example:end -->

The next `budget.check()` raises `BudgetExceeded` at the one-call cap. Only set
`free_local=True` when you know the model call is free; it excludes electricity
and hardware costs. A dollar-only cap cannot bound a free loop. Manual
accounting happens after the response and can overshoot a token cap; it does
not reserve concurrent requests. Do not manually count the same call that a
patch already counts. The explicit event writes JSONL; `consume_billable`
does not emit trace events by itself. For native `/api/chat` and `/api/generate`
responses, see the [native Ollama guide](../cost-guardrails.md#native-ollama-responses),
including the unpublished 1.4.1 candidate's token-field support.

## When Vercel AI Gateway is the right choice

Use a managed gateway when centralized routing and supported-provider failover
fit your workflow. Use local checks when you own the Python dispatch path and
need limits on recorded work, including calls made directly to a local endpoint.
Both need an explicit accounting contract for paid and free calls.

## Summary

These tools can coexist. Check the actual dispatch and billing boundary before
treating either budget as a hard spend limit.
