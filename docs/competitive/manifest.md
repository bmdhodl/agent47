# AgentGuard vs Manifest

This is a living positioning doc. It compares AgentGuard (in-process Python SDK) with Manifest (open-source LLM router with budget caps). Last updated: 2026-05-27.

## Why this comparison exists

[Manifest](https://manifest.build) is an open-source LLM inference optimization platform: a BYOK router that sits in front of OpenAI, Anthropic, Mistral, Ollama, llama.cpp, and any OpenAI-compatible endpoint. It advertises real-time spend visualization, soft and hard budget limits, notifications on limit hits, and replay-and-compare across models. At time of writing it has 6.6k GitHub stars and 27k+ Docker pulls.

Three of those four headline features (spend viz, soft/hard limits, notifications) overlap with AgentGuard's pitch. The confusion is real, so the positioning needs to be sharp: **AgentGuard is not an LLM cost router. It is an in-process agentic-loop guard.** Manifest owns the router framing. AgentGuard owns the in-process runtime-stop framing.

## Comparison

| Axis | AgentGuard | Manifest |
|------|-----------|----------|
| **Deployment model** | In-process Python SDK. Guards run in the same process as the agent and raise exceptions that kill the run. | Network proxy. LLM calls route through a Manifest container (self-hosted via Docker or cloud-hosted). |
| **Primary use case** | Agentic loops: tool use, retries, multi-step reasoning, code-edit agents, autonomous workflows. | Chat and inference workloads behind a unified gateway. |
| **What gets stopped** | The run itself. `BudgetExceeded`, `LoopDetected`, `RetryLimitExceeded`, `TimeoutExceeded` raised in-process. | The next API call, after the proxy declines or alerts. |
| **Loop detection** | First-class. `LoopGuard(max_repeats=N)` catches an agent looping on the same tool with the same args. | Not a feature. Manifest sees independent chat requests, not an agent's call graph. |
| **Where enforcement happens** | At the call site, before the framework dispatches the tool. | At the network hop, after the agent has already decided to call. |
| **Infrastructure required** | None. `pip install agentguard47`. Zero runtime deps. | A running Manifest service (Docker container or hosted), plus client config to route through it. |
| **Local / air-gapped support** | Yes by default. Local JSONL traces. No network calls unless you opt into `HttpSink`. | Self-hostable, so yes — at the cost of running and operating the proxy. |
| **License** | MIT. Free forever. | Open source. Basic version free. |

## What overlaps

Both tools enforce budget caps. Both surface spend. Both can notify on limit. If your problem is "my OpenAI bill from a chat product is unpredictable," Manifest is a clean fit — it does cost control at exactly the layer the cost happens.

## What does not overlap

Manifest does not catch:

- An agent that loops on `search_docs("refund policy")` 80 times in 30 seconds because the response is being misinterpreted upstream.
- A retry storm where the tool succeeds but the agent re-invokes it because the result didn't match its plan.
- A goal that drifts from "fix this test" into "rewrite the test framework" — the calls still look fine at the proxy.
- A 9-second sequence of destructive tool calls (see the PocketOS incident in the [README](../../README.md#real-incidents-agentguard-prevents)) where the issue is the agent's behavior, not the LLM spend.

AgentGuard catches all of those because it lives inside the agent's process and sees the call graph, not just the egress traffic.

## When Manifest is the right choice

If you operate a chat product or RAG service and the problem is **per-tenant or per-key LLM spend**, Manifest is a strong fit. It centralizes routing, gives you a dashboard, lets you replay queries against alternative models, and slots in front of any OpenAI-compatible client. Teams that want a self-hosted alternative to commercial LLM gateways will find it well-shaped.

AgentGuard is the wrong tool for that job. It does not route, cache, or A/B compare models.

## When AgentGuard is the right choice

If the problem is **an agent that can loop, retry, or chain destructive calls**, AgentGuard is the tool. It enforces in-process so the run stops before the next bad call lands, regardless of whether the LLM is OpenAI, a local Ollama, or a model behind Manifest's own router.

The two can compose: AgentGuard inside the agent process for runtime safety, Manifest in front of the LLM provider for cost routing across tenants. They sit at different layers.

## Summary

Manifest = **LLM cost router** at the network layer.
AgentGuard = **agentic-loop guard** at the process layer.

Both reduce surprise spend. Only one of them stops a runaway agent mid-run.
