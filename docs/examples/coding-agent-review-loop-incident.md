# AgentGuard Incident Report

Status: **incident**
Severity: **critical**
Primary cause: **retry_limit_exceeded**

## Summary

- Total events: 14
- Spans: 4
- Events: 9
- Duration: 1.5 ms
- Estimated cost: $0.1020
- Guard events: 2
- Errors: 0
- Exact savings: $0.0000
- Estimated savings: $0.0205

## Savings Ledger

- Exact tokens saved: 0
- Estimated tokens saved: 0
- Exact dollars saved: $0.0000
- Estimated dollars saved: $0.0205
- Savings reasons:
  - `budget_overrun_stopped` (estimated): 0 tokens / $0.0205 across 1 occurrence(s)

## Guard Events

- `guard.budget_exceeded` (critical)
- `guard.retry_limit_exceeded` (critical)

## Recommended Next Steps

- Add exponential backoff or a deterministic fallback before retrying the same tool.
- Treat repeated upstream failures as a stop condition instead of widening the retry ceiling.
- Connect HttpSink to the hosted dashboard for retained alerts and remote kill switch.
- Review the trace timeline to confirm the failure path before widening limits.

## Upgrade Path

Move from one-off local reports to retained alerts, spend history, and remote kill switch:

```python
from agentguard import Tracer, HttpSink

tracer = Tracer(sink=HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_..."))
```
