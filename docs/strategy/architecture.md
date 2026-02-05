# Technical Architecture (MVP)

## Components
- SDK (Python): tracing, guards, and replay primitives
- Local JSONL sink: default storage for traces

## Data model
Event schema:
- trace_id
- span_id
- parent_id
- name
- kind (trace, span, event)
- ts
- duration_ms (if applicable)
- data (arbitrary JSON)

## Core flows
1. Agent run
- Start trace
- Create spans per reasoning step and tool call
- Emit events to JSONL

2. Guarding
- Track tool call signatures
- Detect repeats and raise LoopDetected
- Track token usage and raise BudgetExceeded

3. Replay
- Record request/response pairs
- Load recording and serve stable responses

## Extensibility
- Add sinks (S3, OTLP, HTTP)
- Add framework adapters (LangChain, CrewAI, AutoGen)
