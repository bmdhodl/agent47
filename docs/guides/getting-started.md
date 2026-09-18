# Getting started with AgentGuard

AgentGuard checks limits in instrumented Python code. Installing it alone does
not change another agent's behavior.

## Install and verify

Use Python 3.9 or newer in a virtual environment.

```bash
python -m pip install agentguard47
agentguard doctor
agentguard demo
```

These checks run locally without provider credentials. The commands print
their trace paths. Use those paths with `agentguard report <trace-path>` or
`agentguard incident <trace-path>` to inspect what happened.

The [README budget example](../../README.md#stop-before-a-third-call) is a
complete offline example with an assertion for the stopped call.

## Generate a starter

```bash
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

Run this in a scratch directory. Review generated files before copying them
into your application. Run `agentguard quickstart --help` for supported stacks.
Provider starters require the provider's client and credentials; the raw
starter does not.

## Write a local trace

```python
from agentguard import JsonlFileSink, Tracer

tracer = Tracer(
    service="example",
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
)
with tracer.trace("agent.run") as span:
    span.event("tool.result", data={"result": "example complete"})
```

Inspect the trace:

```bash
agentguard report .agentguard/traces.jsonl
agentguard incident .agentguard/traces.jsonl
```

Only the events you instrument appear in the trace. Review their contents
before sharing a report.

## Add checks at the operation boundary

Call `budget.check()` before a provider request and
`budget.consume(...)` after recording its usage. Stop or change course when
a guard raises. Catching an exception and continuing unchanged defeats the stop.

For OpenAI, install the `openai` package separately, set its credentials, and
configure `patch_openai(tracer, budget_guard=budget)` as shown in the
[README](../../README.md#connect-a-provider). Anthropic has a corresponding
`patch_anthropic` helper.

Provider patches check the recorded budget before dispatch. Response usage
can exceed the remaining allowance; concurrent calls do not reserve capacity.
Streamed OpenAI and Anthropic calls record final usage once. OpenAI streams
request `include_usage` unless the caller already set it. A stream that ends
without usage counts as one call with zero tokens. The OpenAI Responses API
is not patched. Direct SDK clients you do not wrap are a bypass. Subscription
quotas stay with the provider. See the
[enforcement boundary](../enforcement-boundary.md).

For tools, call `LoopGuard.check(tool_name, arguments)` before dispatch.
With a tracer, emit the tool-call event before running the tool. A guard
cannot undo an operation that already happened.

## Choose an integration

- [LangChain](../integrations/langchain.md)
- [LangGraph](../integrations/langgraph.md)
- [CrewAI](../integrations/crewai.md)
- [Coding-agent setup](coding-agents.md)
- [Generated repo instructions](coding-agent-safety-pack.md)
- [Session correlation](managed-agent-sessions.md)
- [Optional hosted ingest](dashboard-contract.md)

Optional extras add dependencies. Check the [security notes](../../README.md#limits-and-security)
before installing them. Local SDK use needs no hosted account or API key.
