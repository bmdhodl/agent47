# Dogfood Proof - 2026-05-29 run3

## Scope

SDK-only recurring dogfood run appended to PR #544 from branch
`dogfood-2026-05-29-run2-worker`.

Base commit before this run: `0ed449844b533fd699ef13a5ca3f8f4592c3cc55`.

Non-goals: no dashboard, auth, billing, deployment, paid-feature, or release
work.

## Commands Run

- `python -m pip install -e ./sdk`
- installed CLI `agentguard doctor --json`
- installed CLI `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --json`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-29/run3/demo_trace_repo_local.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-29/run3/coding_agent_review_loop_traces.jsonl`

All proof commands exited 0. Doctor was rerun after trace filename inspection so
both installed and repo-local raw doctor traces are present in this folder.

## Guard Behavior Observed

`demo_trace_repo_local.jsonl` contains real guard events:

- `guard.budget_warning` at cost used `$0.8400` against limit `$1.0000`
- `guard.budget_exceeded` at `$1.0800 > $1.0000`
- `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2

`coding_agent_review_loop_traces.jsonl` contains real coding-agent enforcement:

- `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3
- `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3

`doctor_trace_repo_local.jsonl` contains the local `doctor.verify` start and
end span.

## Artifacts

- `pip_install_editable.txt`
- `doctor_trace.jsonl`
- `demo_trace.jsonl`
- `doctor_trace_repo_local.jsonl`
- `demo_trace_repo_local.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `demo_report.txt`
- `review_loop_incident.md`
- `doctor_stdout.json`
- `demo_stdout.txt`
- `doctor_repo_local_stdout.json`
- `demo_repo_local_stdout.txt`
- `review_loop_stdout.txt`
- `import_binding.txt`
- `command_status.txt`
- `staleness.log`

## Repo Health

- Repo identity: public `bmdhodl/agent47`, default branch `main`.
- SDK package: local, installed, and PyPI `agentguard47` are `1.2.10`.
- MCP package: local and npm `@agentguard47/mcp-server` are `0.2.2`.
- GitHub release observed: `AgentGuard v1.2.10`, published 2026-05-02.
- Official MCP Registry search still reports `0.2.1` for `io.github.bmdhodl/agentguard47`.
- Glama API returned HTTP 403 from this environment, so tool indexing could not
  be revalidated in this run.
- Ops freshness remains stale by policy: roadmap 3 weeks old, architecture 4
  weeks old, tracked by issue #473.

## PR And Issue State

- PR #544 is green but `REVIEW_REQUIRED` / `BLOCKED`.
- Copilot generated only an overview review on #544; GraphQL review-thread
  sweep returned 0 review threads.
- Rolling issue #490 is the GitHub sink for this run's proof summary.
- Open issue #473 tracks stale ops docs.
- Security issues #507 and #469 still need clean SDK-only reproduction before
  treating scanner output as a core runtime blocker.

## Validation

Recorded after proof generation:

- JSON/JSONL artifact parsing passed.
- Focused proof/metadata tests passed.
- `python scripts/sdk_release_guard.py --check-mcp-npm` passed.
- `git diff --check` passed.
- UTF-8/BOM/NUL/local-path hygiene passed.
