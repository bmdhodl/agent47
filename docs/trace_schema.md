# Trace Schema (MVP)

This schema documents the JSONL events emitted by AgentGuard.

## Event shape
```json
{
  "service": "demo",
  "kind": "span|event",
  "phase": "start|end|emit",
  "trace_id": "<uuid>",
  "span_id": "<uuid>",
  "parent_id": "<uuid|null>",
  "name": "agent.run",
  "ts": 1738690000.123,
  "duration_ms": 1.2,
  "data": {},
  "error": {
    "type": "LoopDetected",
    "message": "Detected repeated tool call search 3 times"
  }
}
```

## Field definitions
- `service`: logical service name (string)
- `kind`: `span` for start/end records, `event` for point-in-time events
- `phase`: `start`, `end`, or `emit`
- `trace_id`: correlation ID for a full run
- `span_id`: unique ID for a span or event
- `parent_id`: parent span ID, null for root
- `name`: semantic name (e.g., `agent.run`, `tool.result`)
- `ts`: unix timestamp in seconds
- `duration_ms`: populated on span end
- `data`: arbitrary JSON payload
- `error`: optional error object

## Conventions
- A root span (`agent.run`) should emit a start and end record.
- Reasoning steps should use `reasoning.step`.
- Tool calls should use `tool.start` / `tool.end` or `tool.result`.
