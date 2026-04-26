# Dashboard Contract

Use this when you move from local SDK proof to the hosted AgentGuard dashboard.

The product boundary is deliberate:
- the SDK owns local runtime enforcement, local traces, local reports, and
  structured event emission
- the dashboard owns retained history, alerts, team workflows, billing, and
  remote kill signal management

## First path

Keep first adoption local:

```bash
pip install agentguard47
agentguard doctor
agentguard demo
agentguard quickstart --framework raw
```

Only add hosted ingest after the local guard path works.

## Hosted ingest

Send traces to:

```text
https://app.agentguard47.com/api/ingest
```

The SDK sends newline-delimited JSON. Hosted ingest accepts only trace records
with:
- `kind` of `span` or `event`
- `type` mirroring `kind`
- required trace envelope fields such as `service`, `phase`, `trace_id`,
  `span_id`, `name`, and `ts`

`HttpSink` normalizes outbound events for this contract:
- local-only metadata records such as the watermark are not posted
- supported records carry both `kind` and `type`
- network failures are logged instead of crashing the calling agent
- retries are bounded by `max_retries`

## Decision history

Decision traces are ordinary AgentGuard events. The hosted dashboard recognizes
these event names:

- `decision.proposed`
- `decision.edited`
- `decision.overridden`
- `decision.approved`
- `decision.bound`

Each decision payload must include:

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

The SDK helpers emit dashboard-parseable `binding_state` values by default:
- `decision.proposed` -> `proposed`
- `decision.edited` -> `edited`
- `decision.overridden` -> `overridden`
- `decision.approved` -> `approved`
- `decision.bound` -> caller-provided state such as `applied`, `merged`, or
  `failed`

For the full helper API, see [`decision-tracing.md`](decision-tracing.md).

## Remote kill signals

The dashboard exposes remote kill signal APIs, including polling by `trace_id`
and acknowledgment after a runtime handles a signal.

Current SDK behavior:
- `HttpSink` does not poll for kill signals
- `agentguard.init(api_key=...)` sends traces but does not execute remote kill
  signals
- local guards remain the authoritative way to stop a runaway agent in-process

If an application implements dashboard kill polling directly, keep it bounded:
- poll with short HTTP timeouts
- treat network errors as no-op unless the application explicitly chooses a
  fail-closed policy
- acknowledge handled signals through the dashboard API
- keep `BudgetGuard`, `LoopGuard`, `RetryGuard`, and `TimeoutGuard` enabled
  locally

Do not present remote kill as active in an SDK integration unless the runtime
has explicit polling and handling code.
