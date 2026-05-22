# AgentGuard Dogfood Proof - 2026-05-22 run5

## Scope

- SDK-only dogfood run.
- No dashboard, auth, billing, deployment, release, or paid-feature code touched.
- Proof was bound to the repo-local SDK by setting `PYTHONPATH=./sdk`.

## Commands

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-22/run5/agentguard_demo_traces-run5.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-22/run5/coding_agent_review_loop_traces-run5.jsonl`

All commands exited `0`.

## Raw Artifacts

- `agentguard_doctor_trace-run5.jsonl`
- `agentguard_demo_traces-run5.jsonl`
- `coding_agent_review_loop_traces-run5.jsonl`
- `agentguard-doctor-run5.txt`
- `python-doctor-run5.txt`
- `demo-run5.txt`
- `review-loop-run5.txt`
- `demo-report-run5.md`
- `review-loop-incident-run5.md`
- `guard-events-run5.json`
- `repo-import-run5.txt`

## Guard Behavior Observed

The run showed real AgentGuard enforcement in raw JSONL traces.

`agentguard_demo_traces-run5.jsonl` emitted:

- `guard.budget_warning` at `$0.8400 / $1.0000`
- `guard.budget_exceeded` at `$1.0800 > $1.0000`
- `guard.loop_detected` for repeated `search` calls
- `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2

`coding_agent_review_loop_traces-run5.jsonl` emitted:

- `guard.budget_exceeded` on review attempt 3 at `$0.0510 > $0.0450`, with cumulative spend recorded as `cost_used_usd` so report totals do not double-count it
- `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3

`agentguard_doctor_trace-run5.jsonl` emitted setup-validation trace events. It is included as install/setup proof, not enforcement proof.

## Enforcement Verdict

Real enforcement confirmed. This run is not counted from command success alone; the raw traces contain concrete budget, loop, and retry guard events.

## Repo Health Notes

- Roadmap freshness command returned `13 days ago`.
- Architecture freshness command returned `3 weeks ago`.
- Existing tracker for docs freshness remains issue #473.
- `ops/FOLLOWUP.md` still points to Glama indexing and official MCP Registry metadata drift.
- `NIGHTLY_QUEUE.md` was not present.
