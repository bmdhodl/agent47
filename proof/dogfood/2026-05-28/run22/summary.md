# AgentGuard Dogfood Run 22 - 2026-05-28



## Scope



- Repo: `bmdhodl/agent47`

- Branch/PR: `dogfood-2026-05-28-run15-worker` / PR #542

- SDK scope only: proof artifacts for the local AgentGuard dogfood path

- Non-goals: no runtime SDK changes, no dashboard/auth/billing/deployment work, no release



## Commands Run



- `agentguard doctor --trace-file proof/dogfood/2026-05-28/run22/installed_doctor_trace.jsonl`

- `agentguard demo --trace-file proof/dogfood/2026-05-28/run22/installed_demo_trace.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run22/doctor_trace.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run22/demo_trace.jsonl`

- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`

- `PYTHONPATH=./sdk python -m agentguard.cli report --json proof/dogfood/2026-05-28/run22/demo_trace.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run22/demo_trace.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli report --json proof/dogfood/2026-05-28/run22/coding_agent_review_loop_traces.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run22/coding_agent_review_loop_traces.jsonl`

- `PYTHONPATH=./sdk python -m agentguard.cli incident --format json proof/dogfood/2026-05-28/run22/coding_agent_review_loop_traces.jsonl`



All command exit codes were `0`; see `command_status.json`.



## Guard Behavior Observed



Trace inspection found 22 guard/demo events and all required guard event names:



- `guard.budget_warning`

- `guard.budget_exceeded`

- `guard.loop_detected`

- `guard.retry_limit_exceeded`



The repo-local demo enforced:



- BudgetGuard warning at 84% of the $1.00 demo limit.

- BudgetGuard stop at `$1.08 > $1.00`.

- LoopGuard stop for repeated `tool.search({"query":"python asyncio"})`.

- RetryGuard stop for `fetch_docs` after retry attempt 3 with limit 2.



The coding-agent review-loop proof enforced:



- BudgetGuard stopped the review loop on attempt 3 at `$0.0510 > $0.0450`.

- RetryGuard stopped the `apply_patch` retry storm on attempt 4 with limit 3.



## Enforcement Verdict



Real enforcement observed. This run counts as dogfood proof because the raw JSONL traces contain guard events and the command output shows the guards stopping budget, loop, and retry behavior.



## Files



- `installed_doctor_trace.jsonl`

- `installed_demo_trace.jsonl`

- `doctor_trace.jsonl`

- `demo_trace.jsonl`

- `coding_agent_review_loop_traces.jsonl`

- `guard_events.json`

- `guard_event_summary.json`

- `demo_report.json`

- `demo_incident.md`

- `review_loop_report.json`

- `review_loop_incident.md`

- `review_loop_incident.json`

- `command_status.json`

- command output transcripts

