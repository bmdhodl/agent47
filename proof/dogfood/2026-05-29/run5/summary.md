# AgentGuard dogfood run5 - 2026-05-29

## Scope

- Goal: keep the AgentGuard SDK dogfood path active with fresh trace-backed proof.
- Scope: proof-only artifacts under `proof/dogfood/2026-05-29/run5/`.
- Non-goals: no SDK feature work, dashboard work, auth, billing, secrets, deployments, or release cutting.
- Done criteria: local guard enforcement is observable in raw traces, outputs are materialized in-repo, validation passes, and the rolling GitHub proof sink is updated.

## Commands run

- `python -m pip install -e ./sdk`
- `agentguard doctor --trace-file proof/dogfood/2026-05-29/run5/doctor_trace.jsonl --json`
- `agentguard demo --trace-file proof/dogfood/2026-05-29/run5/demo_trace.jsonl`
- `agentguard report proof/dogfood/2026-05-29/run5/demo_trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `agentguard report proof/dogfood/2026-05-29/run5/coding_agent_review_loop_traces.jsonl`
- `agentguard incident proof/dogfood/2026-05-29/run5/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run5/doctor_trace_repo_local.jsonl --json`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-29/run5/demo_trace_repo_local.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-29/run5/demo_trace_repo_local.jsonl`

All proof commands exited 0. See `command_status.txt`.

## Guard behavior observed

Real enforcement was observed in trace output, not inferred from command success:

- `demo_trace.jsonl`: `guard.budget_warning` at `$0.84 / $1.00`.
- `demo_trace.jsonl`: `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- `demo_trace.jsonl`: `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- `demo_trace.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` on review attempt 3 at `$0.0510 > $0.0450`.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- `demo_trace_repo_local.jsonl`: same budget, loop, and retry enforcement as the installed CLI path.

The extracted event list is saved in `guard_events.json`.

## Repo health

- Repo identity: `bmdhodl/agent47`, dogfood PR branch `dogfood-2026-05-29-run2-worker`.
- PR #544 is mergeable with green CI/CodeQL, zero review threads, and required human review still blocking merge.
- Open dogfood proof PRs remain queued behind human review; no actionable automated comments appeared on #544.
- Release/package alignment: GitHub release and PyPI are `1.2.10`; local SDK is `1.2.10`; npm MCP package is `0.2.2`.
- Distribution blockers persist: Official MCP Registry still reports `0.2.1`; Glama still reports `tools: []`.

## Freshness

- Roadmap: 3 weeks old.
- Architecture: 4 weeks old.
- Existing tracker: https://github.com/bmdhodl/agent47/issues/473.

## Artifacts

- Raw traces: `doctor_trace.jsonl`, `demo_trace.jsonl`, `coding_agent_review_loop_traces.jsonl`, `doctor_trace_repo_local.jsonl`, `demo_trace_repo_local.jsonl`.
- Command output: `doctor_stdout.json`, `demo_stdout.txt`, `review_loop_stdout.txt`, reports, incident output, and stderr files.
- Health evidence: `github_release.json`, `pypi_versions.txt`, `npm_mcp_version.json`, `official_mcp_registry.json`, `glama.json`, `staleness.log`.

## Next task

Merge or review the green proof PR queue, starting with #544, then do the narrow ops-doc freshness pass tracked by #473.
