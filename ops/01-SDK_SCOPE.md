# SDK Scope & Ownership

## SDK owns (this repo, MIT, free)

- **Runtime guards** — loop, budget, timeout, rate-limit detection with exception-based enforcement
- **Structured tracing** — Tracer, TraceContext, spans, events in JSONL format
- **Cost estimation** — per-model pricing lookup, no network calls
- **Framework integrations** — LangChain, LangGraph, CrewAI callbacks
- **LLM client patching** — OpenAI, Anthropic (sync + async)
- **Trace sinks** — file, stdout, HTTP, OpenTelemetry
- **Evaluation framework** — EvalSuite for offline trace assertions
- **CLI** — `agentguard report`, `agentguard summarize`, `agentguard eval`
- **MCP server** — TypeScript, read-only trace query tools

## Dashboard owns (private repo `agent47-dashboard`, BSL 1.1, paid)

- Trace storage and querying
- Alerting and notification rules
- Remote kill switch
- Team management and access control
- Billing and subscriptions
- Web UI (timeline, cost dashboards, agent health)

## Boundary contract

- **SDK -> Dashboard:** `HttpSink` pushes events to `/api/v1/events` (gzip, batched, retried). Auth via `AGENTGUARD_API_KEY` header.
- **Dashboard -> SDK:** No reverse dependency. Dashboard reads events; SDK never calls dashboard APIs.
- **MCP Server -> Dashboard:** Read-only queries to `/api/v1/` endpoints (traces, alerts, usage, costs).

## What the SDK will never do

- Require network access to function (all guards work offline)
- Add hard dependencies (stdlib only in core; framework deps optional)
- Phone home, collect telemetry, or require authentication for local use
