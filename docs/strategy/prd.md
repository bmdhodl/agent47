# Product Requirements (MVP)

## Target user
Solo developers and small teams building multi-agent workflows who need to debug and validate behavior without heavy tooling.

## Primary jobs-to-be-done
- Understand why an agent made a specific decision
- Prevent costly loops and runaway tool usage
- Reproduce a run deterministically for tests

## MVP features
1. Trace capture
- Capture prompt, tool call, tool output, and decision steps
- Correlate steps with a trace_id and span_id
- Export to JSONL locally

2. Loop and cost guards
- Detect repeated tool calls with identical arguments
- Allow budget caps by token count or call count
- Provide clear failure reasons and stop execution

3. Replay
- Record real runs and replay deterministically
- Create stable regression tests independent of model output

## Out of scope
- Hosted dashboard
- Fine-grained permission model
- Alerts and paging

## Success metrics
- Time-to-first-trace < 5 minutes
- 50% reduction in “mystery failures” for users
- 10 OSS stars in the first 30 days after launch
