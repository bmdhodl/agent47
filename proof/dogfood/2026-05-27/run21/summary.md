# AgentGuard dogfood run21

Date: 2026-05-27
Branch: dogfood-2026-05-27-run9-worker
Commit before run: d678be3

## Commands

- `agentguard doctor --trace-file agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file agentguard_demo_traces.jsonl`
- `py -3.11 -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `py -3.11 -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `py -3.11 examples/coding_agent_review_loop.py`
- `py -3.11 -m agentguard.cli report agentguard_demo_traces.jsonl`
- `py -3.11 -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

All recorded command exit files are `0`.

## Raw Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- command stdout, stderr, and exit files

## Guard Behavior Observed

Demo trace:

- `guard.budget_warning` at `0.84 / 1.00` USD.
- `guard.budget_exceeded` at `1.08 > 1.00` USD.
- `guard.loop_detected` for repeated `search` calls.
- `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.

Review-loop trace:

- `guard.budget_exceeded` stopped the loop at `0.0510 > 0.0450` USD.
- `guard.retry_limit_exceeded` stopped `apply_patch` at attempt 4 with limit 3.

## Enforcement Assessment

Enforcement was real. The proof is not based only on process exit codes: the JSONL traces contain guard events showing budget, loop, and retry enforcement, and the review-loop trace contains hard stops for budget and retry exhaustion.
