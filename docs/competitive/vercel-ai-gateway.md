# AgentGuard vs Vercel AI Gateway

This is a living positioning doc. It compares AgentGuard (in-process Python SDK) with Vercel AI Gateway (hosted proxy layer). Last updated: 2026-04-13.

## Why this comparison exists

Vercel launched AI Gateway as a proxy that sits between your app and LLM providers. It offers budgets, routing, caching, and rate limiting for AI calls routed through Vercel's infrastructure.

AgentGuard does budget enforcement and loop detection too. But it runs inside your process, not as a network hop. The architectures are fundamentally different and the right choice depends on where your agent runs and what you control.

Vercel reported that 30% of deployments on their platform are now agent-initiated, with Claude Code accounting for 75% of those. Their AI Gateway explicitly advertises "budgets and routing" as features. This is the same problem space AgentGuard operates in.

## Comparison

| Axis | AgentGuard | Vercel AI Gateway |
|------|-----------|-------------------|
| **Deployment model** | In-process Python SDK. Runs in the same process as your agent. | Gateway proxy. All LLM calls route through Vercel's infrastructure. |
| **Provider lock-in** | None. Works with any LLM provider, any model, any inference endpoint. `patch_openai()`, `patch_anthropic()`, or manual `consume()` calls. | Routes through Vercel's backend. Works with providers Vercel supports. Your billing relationship is with Vercel. |
| **Local-first** | Yes. Runs on your laptop, your RTX 5070 Ti, your on-prem server, your CI runner. No network calls required. | Cloud-only. Requires Vercel deployment. Cannot run on local hardware or air-gapped environments. |
| **Latency overhead** | Zero. Guards execute in-process. No extra network hop. | One additional round-trip per LLM call through the gateway proxy. |
| **Governance** | You own the audit log. JSONL traces on your filesystem. Export to your own storage. | Vercel hosts the audit log. You access it through their dashboard and API. |
| **Dependencies** | `pip install agentguard47`. Zero runtime dependencies. Python stdlib only. | Vercel account, team, billing relationship, and deployment infrastructure. |
| **Price** | Free. MIT license. Forever. | Usage-based Vercel pricing on top of LLM provider costs. |

## Worked scenario: Claude Code with local Ollama fallback

You run Claude Code on Vercel for production workloads. For development and testing, you run Ollama locally on a consumer GPU to save money.

**With Vercel AI Gateway:** Your production calls route through the gateway and get budget tracking. Your local Ollama calls do not go through the gateway. You have two different enforcement models, or you skip enforcement locally.

**With AgentGuard:**

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink, patch_anthropic, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"))

# Same guards work for both providers
# Production: patch_anthropic(tracer, budget_guard=budget) for Claude
# Dev: patch_openai(tracer, budget_guard=budget) for local Ollama via OpenAI-compatible API
```

One SDK. Same budget enforcement whether the call goes to Claude's API or to localhost:11434. Same trace format. Same audit log. The guard does not care where the model lives.

## When Vercel AI Gateway is the right choice

If your entire stack already runs on Vercel and you want centralized LLM routing with caching, Vercel AI Gateway is a reasonable choice. It handles provider failover and response caching at the infrastructure layer without touching your application code. Teams that are all-in on Vercel's platform and do not need local enforcement or on-prem support will find the gateway convenient. AgentGuard is the better fit when you need runtime enforcement that works everywhere your code runs, not just on one platform.

## Summary

AgentGuard and Vercel AI Gateway solve overlapping problems from different layers. AI Gateway is infrastructure. AgentGuard is application-level runtime safety. They can coexist. But if you need guards that work on your laptop, in CI, on bare metal, and in the cloud with zero vendor lock-in, AgentGuard is the tool that runs everywhere your agent does.
