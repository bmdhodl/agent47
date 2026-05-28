# AgentGuard Dogfood Run 6 - 2026-05-28

## Scope

- Repo: `bmdhodl/agent47`
- Branch: `dogfood-2026-05-28-run6-worker`
- Proof directory: `proof/dogfood/2026-05-28/run6/`
- Runtime: 2026-05-28 02:50-02:51 America/Chicago
- Goal: prove repo-local AgentGuard guard enforcement with durable raw traces, reports, and parsed guard events.

## Commands Run

The full command inventory and exit codes are in `command-status.txt` and `validation-status.txt`.

- `agentguard doctor --trace-file proof/dogfood/2026-05-28/run6/installed_doctor_traces.jsonl --json`
- `agentguard demo --trace-file proof/dogfood/2026-05-28/run6/installed_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run6/repo_doctor_traces.jsonl --json`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run6/repo_demo_traces.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-28/run6/repo_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-28/run6/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident --format json proof/dogfood/2026-05-28/run6/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run6/coding_agent_review_loop_traces.jsonl`

## Guard Behavior Observed

Parsed event inventory is saved in `guard_events.json`.

- `repo_demo_traces.jsonl`: `guard.budget_warning` at `$0.84 / $1.00`.
- `repo_demo_traces.jsonl`: `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- `repo_demo_traces.jsonl`: `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- `repo_demo_traces.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs` attempted 3 times with limit 2.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` on attempt 3 at `$0.0510 > $0.0450`.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

This is real enforcement proof, not command-only success: the raw traces contain guard events, and the review-loop stdout shows BudgetGuard and RetryGuard stopping the simulated coding-agent workflow.

## Repo Health Notes

- Installed `agentguard` imports from a stale external checkout, so installed CLI output is retained as smoke evidence only.
- Repo-local proof is canonical and was run with `PYTHONPATH=./sdk`.
- GitHub release and PyPI latest are `agentguard47 v1.2.10`.
- npm latest for `@agentguard47/mcp-server` is `0.2.2`.
- Roadmap and architecture are stale by repo policy: roadmap last changed 3 weeks ago; architecture last changed 4 weeks ago. This remains tracked by issue `#473`.
- The review-loop report still shows `Estimated cost: $0.1020` for a `$0.0510` enforced stop on `main`. PR `#502` already fixes the cost-accounting payload and is green but waiting on human review.

## Validation

- Focused dogfood pytest slice: 35 passed.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Artifact hygiene scan: passed; exact checklist and command shape are saved in `artifact_hygiene_command.txt`.

## Docs Updates Needed

No SDK docs update is needed for this proof-only run. The next non-proof repo task is still ops/doc freshness or merging PR `#502`.
