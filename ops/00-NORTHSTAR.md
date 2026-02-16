# AgentGuard SDK — North Star

## What it is

A zero-dependency Python SDK that gives AI agent builders runtime guards — hard budget limits, loop detection, and timeout enforcement that kill agents mid-run before they cause damage.

## Who it's for

Python developers building autonomous agent systems with LangChain, LangGraph, CrewAI, or raw OpenAI/Anthropic APIs — especially those moving agents from prototype to production.

## What problem it solves

Agents fail silently. They loop, overspend, and hang. AgentGuard intercepts these failures at runtime with structured tracing and guards that raise exceptions — not dashboards that show you the damage after it happened.

## Non-goals

1. **Not a framework.** We don't orchestrate agents. We guard whatever framework you already use.
2. **Not an observability platform.** We emit structured traces (JSONL) but don't store, query, or visualize them. Sinks push traces elsewhere (files, HTTP, OpenTelemetry).
3. **Not a prompt engineering tool.** We don't evaluate prompt quality or optimize outputs. We stop agents from burning money and looping.
