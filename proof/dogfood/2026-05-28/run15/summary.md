# Dogfood Proof - 2026-05-28 run15

## Repo State

- Branch: `dogfood-2026-05-28-run15-worker`
- Base commit: `b0e872025e0b0980555ad5b3d376ec28f481744b`
- SDK import binding: active checkout via `PYTHONPATH=./sdk`
- Installed CLI smoke: `agentguard` exists on PATH, but the ambient Python import resolves to a stale checkout, so the proof commands used `python -m agentguard.cli` with the repo-local SDK path.

## Commands Run

- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run15/agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run15/agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- copy `coding_agent_review_loop_traces.jsonl` into `proof/dogfood/2026-05-28/run15/`
- `python -m agentguard.cli report --json proof/dogfood/2026-05-28/run15/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report --json proof/dogfood/2026-05-28/run15/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run15/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident --format json proof/dogfood/2026-05-28/run15/coding_agent_review_loop_traces.jsonl`

Full command output is in `command-status.txt` plus the per-command `*.out.txt`, `*_report.json`, and incident files in this folder.

## Guard Behavior Observed

Real enforcement was observed in emitted trace events, not inferred from exit codes.

- `agentguard_demo_traces.jsonl`
  - `guard.budget_warning`: warning fired at 84% of a 1.00 USD budget.
  - `guard.budget_exceeded`: BudgetGuard stopped spend at 1.08 USD over a 1.00 USD limit.
  - `guard.loop_detected`: LoopGuard stopped repeated `tool.search` calls.
  - `guard.retry_limit_exceeded`: RetryGuard stopped `fetch_docs` after the retry ceiling.
- `coding_agent_review_loop_traces.jsonl`
  - `guard.budget_exceeded`: BudgetGuard stopped the review loop on attempt 3 at 0.0510 USD over a 0.0450 USD limit.
  - `guard.retry_limit_exceeded`: RetryGuard stopped repeated `apply_patch` retries on attempt 4 with a limit of 3.

The extracted guard-event payloads are in `guard_events.json`.

## Result

Dogfood proof passed. The active-checkout proof path exercised local AgentGuard enforcement for budget, loop, and retry behavior, and the coding-agent review-loop path produced an incident report from the generated trace.

Note: current `main` still renders the review-loop report/incident estimated cost as 0.1020 USD because the guard event also carries cumulative cost. The raw guard stop remains real at 0.0510 USD over a 0.0450 USD limit, and the cost-accounting fix is already represented by the existing review-loop cost PR.
