# Decision Tracing

Use decision traces when an agent proposes an action and a human or downstream
system can edit, override, approve, or bind that action later.

AgentGuard keeps this narrow:
- no new transport
- no new storage dependency
- no graph or embedding logic
- just structured events through the normal `TraceContext.event()` pipeline

## Event types

AgentGuard emits five stable decision event names:

- `decision.proposed`
- `decision.edited`
- `decision.overridden`
- `decision.approved`
- `decision.bound`

Each event is a normal AgentGuard event with the decision schema stored in
`event.data`.

## Required decision fields

Every emitted decision event includes these keys in `data`:

- `decision_id`
- `workflow_id`
- `trace_id`
- `object_type`
- `object_id`
- `actor_type`
- `actor_id`
- `event_type`
- `proposal`
- `final`
- `diff`
- `reason`
- `comment`
- `timestamp`
- `binding_state`
- `outcome`

`trace_id` is duplicated into the decision payload on purpose so downstream
systems can query decision events without reconstructing context from the outer
trace envelope.

## Smallest useful flow

```python
from agentguard import JsonlFileSink, Tracer, decision_flow

tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="approval-flow",
)

with tracer.trace("agent.run") as run:
    with decision_flow(
        run,
        workflow_id="deploy-approval",
        object_type="deployment",
        object_id="deploy-042",
        actor_type="agent",
        actor_id="release-bot",
    ) as decision:
        decision.proposed({"action": "deploy", "environment": "staging"})
        decision.edited(
            {"action": "deploy", "environment": "production"},
            actor_type="human",
            actor_id="reviewer-123",
            reason="Customer approved direct rollout",
            comment="Promoting immediately",
        )
        decision.approved(actor_type="human", actor_id="reviewer-123")
        decision.bound(
            actor_type="system",
            actor_id="deploy-api",
            binding_state="applied",
            outcome="success",
        )
```

This works with:
- `JsonlFileSink`
- `StdoutSink`
- `HttpSink`
- any custom sink that already consumes AgentGuard events

## Low-level helpers

If you do not want the stateful wrapper, emit the events directly:

```python
from agentguard import log_decision_proposed, log_decision_overridden

with tracer.trace("agent.run") as span:
    proposed = log_decision_proposed(
        span,
        workflow_id="ticket-review",
        object_type="ticket",
        object_id="ticket-7",
        actor_type="agent",
        actor_id="triage-bot",
        proposal={"action": "close_ticket"},
    )

    log_decision_overridden(
        span,
        decision_id=proposed["decision_id"],
        workflow_id="ticket-review",
        object_type="ticket",
        object_id="ticket-7",
        actor_type="human",
        actor_id="support-lead",
        proposal=proposed["proposal"],
        final={"action": "escalate_ticket"},
        reason="Customer is still blocked",
        comment="Escalating instead of closing",
    )
```

## Diff behavior

`decision.edited` and `decision.overridden` compute a unified diff by default:

- strings diff as text
- dicts and lists diff as normalized JSON
- if you already have a domain-specific diff, pass it explicitly with `diff=...`

The event always retains both:
- `proposal`: the original proposal
- `final`: the human-modified or overridden form

## Migration notes

No migration is required.

Decision traces are ordinary AgentGuard events:
- existing trace files stay valid
- existing sinks keep working
- existing dashboards or downstream processors can opt into the new event names
- apps can adopt the new helpers incrementally inside one approval workflow at a time

## Example

See [`examples/decision_trace_workflow.py`](../../examples/decision_trace_workflow.py)
for a full local example.
