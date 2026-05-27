# AgentGuard dogfood proof - 2026-05-27 run19

## Commands run

- `agentguard doctor --trace-file agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

## Guard behavior observed

- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo incident classified the run as `Status: incident`, `Severity: critical`, primary cause `loop_detected`.
- Review-loop trace emitted `guard.budget_exceeded` at total cost `$0.0510 > $0.0450` and `guard.retry_limit_exceeded` for `apply_patch` attempt 4.
- Review-loop incident classified the run as `Status: incident`, `Severity: critical`, primary cause `retry_limit_exceeded`.

## Enforcement verdict

Real enforcement observed. This proof is not command-output-only: raw JSONL traces and incident output contain guard stop events for budget, loop, and retry behavior.

## Files in this bundle

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard-events.json`
- `trace_inspection.md`
- command output files: `installed-doctor.txt`, `repo-doctor.txt`, `repo-demo.txt`, `review-loop.txt`, `demo-report.txt`, `demo-incident.txt`, `review-loop-incident.txt`
