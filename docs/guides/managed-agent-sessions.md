# Managed-Agent Sessions

Use `session_id` when one higher-level agent session can span multiple tracer
instances, processes, or disposable harness containers.

This is the pattern you hit with managed-agent architectures:
- one durable user or task session
- multiple short-lived harness runs
- one shared need for guardrail and trace correlation

AgentGuard already gives every top-level trace its own `trace_id`. `session_id`
adds one level above that, so downstream systems can group multiple traces that
belong to the same managed-agent session.

## When to use it

Use `session_id` when:
- your harness can restart between turns
- one user task can fan out across multiple worker processes
- you want local JSONL traces or hosted ingest events to be correlated above
  the single-trace level

Do not use it as a static repo default in `.agentguard.json`. It should be
supplied dynamically by the runtime that knows the actual session boundary.

## Minimal pattern

```python
from agentguard import JsonlFileSink, Tracer

session_id = "support-session-001"

tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="managed-harness-a",
    session_id=session_id,
)

with tracer.trace("harness.turn") as span:
    span.event("decision.proposed", data={"tool": "search_docs"})
```

If another harness picks up the same session later, reuse the same
`session_id`:

```python
from agentguard import JsonlFileSink, Tracer

tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="managed-harness-b",
    session_id="support-session-001",
)
```

Now both harness runs still get their own `trace_id`, but every emitted span
and point event also carries `session_id="support-session-001"`.

## With `agentguard.init()`

If you use the one-liner setup path:

```python
import agentguard

agentguard.init(
    service="managed-harness-a",
    session_id="support-session-001",
    local_only=True,
)
```

This keeps the first proof local while still adding session-level correlation
to the emitted events.

## Local proof

Run the local example that simulates two disposable harnesses sharing one
session:

```bash
python examples/disposable_harness_session.py
```

That writes `managed_session_traces.jsonl` and shows that both harnesses
emitted events with the same `session_id`.

## Boundary

`session_id` is correlation only:
- it does not change guard behavior
- it does not require the hosted dashboard
- it does not make AgentGuard provider-specific

It is just the missing SDK field for managed-agent architectures where the
session boundary is wider than one tracer instance.
