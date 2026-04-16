# Where AgentGuard Fits in the Agent Security Stack

This is a living positioning doc. It explains how AgentGuard fits beside other
emerging agent-security layers rather than pretending one product should do
everything. Last updated: 2026-04-16.

## Why this comparison exists

The agent-security market is fragmenting into layers:

- identity and credential control for non-human identities (NHIs)
- MCP governance and tool-access policy
- sandboxing and isolation for untrusted execution
- runtime budget and behavior controls inside the agent process

AgentGuard belongs in the last layer. It is not an NHI broker, an MCP policy
engine, or a sandbox. It is the in-process runtime-safety layer that stops
loops, retries, timeout overruns, and budget burn while the agent is still
running.

That distinction matters because these layers solve different failure modes.
Trusted credentials do not stop a retry storm. Tool-governance policy does not
kill a stuck loop already running inside the process. A sandbox can contain
damage, but it does not enforce a dollar budget or halt a runaway decision flow
on its own.

## Layer map

| Layer | What it controls | Example category | Where AgentGuard fits |
|------|-------------------|------------------|-----------------------|
| **Identity / NHI** | Which non-human agent, service, or tool invocation is allowed to authenticate and receive credentials | Cloudflare-style NHI / access layer | AgentGuard assumes the agent already has whatever credentials it is allowed to use |
| **MCP governance** | Which MCP servers, tools, approvals, or policies an agent is allowed to invoke | MCPTotal-style MCP governance layer | AgentGuard can trace outcomes, but it does not own remote MCP policy |
| **Isolation / sandbox** | What the agent can execute, touch, or escape from at the host/runtime boundary | IronClaw-style isolation layer | AgentGuard does not virtualize or isolate code execution |
| **Runtime behavior / budget** | Whether the current run is exceeding spend, looping, retrying, timing out, or drifting through risky decision flows | AgentGuard | This is the SDK's core lane |

## The practical framing

If you adopt "non-human identity" language, AgentGuard should not claim to be
the identity layer. The better framing is:

> Once a non-human identity is trusted and issued credentials, AgentGuard is
> the runtime layer that constrains what that agent can do with them while the
> run is live.

That keeps the repo aligned with its real architecture:

- `Tracer` and `AsyncTracer` run in-process
- guards raise exceptions immediately
- local JSONL traces and local proof still work with no network access
- MCP remains a read path for traces and incidents, not the enforcement plane

## Worked scenario

A coding agent gets a valid non-human identity, is allowed to call a small set
of MCP tools, and runs inside a sandboxed worker.

Three different failures can still happen:

1. The identity layer correctly authenticates the agent, but the agent burns
   through the run budget with repeated retries.
2. MCP governance correctly approves a tool call, but the agent gets stuck in
   an A-B-A-B tool loop after the call returns.
3. The sandbox correctly contains filesystem access, but the agent keeps
   spawning expensive model turns until the run is no longer economical.

Those are AgentGuard failures to prevent. They happen after identity,
governance, and isolation have all done their jobs.

```python
from agentguard import BudgetGuard, LoopGuard, RetryGuard, Tracer

tracer = Tracer(
    service="coding-agent",
    guards=[
        BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8),
        LoopGuard(max_repeats=3),
        RetryGuard(max_retries=3),
    ],
)
```

This is why the SDK wedge remains narrow: runtime behavior control is already a
big enough problem without pretending the SDK is the whole agent-security
stack.

## What AgentGuard should say publicly

- We are the runtime budget and behavior layer for coding agents.
- We complement identity, governance, and isolation controls.
- We run where the agent runs: laptop, CI, on-prem, or cloud.
- We are not the credential layer, the sandbox, or the control plane.

## Summary

The clean positioning is not "AgentGuard versus every other security product."
It is "AgentGuard is the runtime layer in a layered agent-security stack."

If Cloudflare-style NHI products answer "who is this agent?", and MCP
governance answers "what tools may it invoke?", and sandboxing answers "what
can it touch?", AgentGuard answers "should this run keep going right now?"
