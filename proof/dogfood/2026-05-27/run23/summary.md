# Dogfood Proof - 2026-05-27 run23

## Scope

This run exercised AgentGuard from the public SDK checkout and refreshed the rolling dogfood proof bundle. No SDK runtime, dashboard, auth, billing, secret, deployment, or release code changed.

## Environment

- Repo: `bmdhodl/agent47`
- Branch: `dogfood-2026-05-27-run9-worker`
- Base proof sink: PR #529 and issue #490
- Local time: 2026-05-27 America/Chicago
- Global `agentguard` shim exists, but default Python import still resolves outside this checkout. Checkout-bound proof used `PYTHONNOUSERSITE=1` and `PYTHONPATH=./sdk`.

## Commands Run

- `agentguard doctor --trace-file agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

All command exit codes are captured in `*.exit.txt` files in this bundle.

## Raw Trace Files

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `global_agentguard_doctor_trace.jsonl`
- `global_agentguard_demo_traces.jsonl`

## Guard Events Observed

Checkout-bound demo trace emitted real guard behavior:

- `guard.budget_warning`: cost used `0.84`, limit `1.0`
- `guard.budget_exceeded`: cost used `1.08`, limit `1.0`, message `Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})` 3 times in the configured window
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Checkout-bound coding-agent review-loop trace emitted real enforcement:

- `guard.budget_exceeded`: attempt 3 stopped at `$0.0510 > $0.0450`, tokens used `12300`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 stopped with limit 3

Doctor trace emitted two `doctor.verify` events.

## Reports

- Demo report: `demo-report.md`
- Demo incident: `demo-incident.md`
- Review-loop incident: `review-loop-incident.md`
- Parsed guard events: `guard_events.json`

## Enforcement Verdict

Real enforcement confirmed. The demo trace shows budget, loop, and retry guard events. The review-loop trace shows a budget stop and retry stop in the repo-local coding-agent workflow.