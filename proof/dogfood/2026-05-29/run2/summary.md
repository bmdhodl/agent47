# Dogfood Proof - 2026-05-29 run2

## Scope

SDK-only recurring dogfood run from `origin/main` at `b0e872025e0b0980555ad5b3d376ec28f481744b`.

Non-goals: no dashboard, auth, billing, deployment, paid-feature, or release work.

## Commands Run

- `python -m pip install -e ./sdk`
- installed CLI `agentguard doctor --json`
- installed CLI `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --json`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-29/run2/demo_trace_repo_local.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-29/run2/coding_agent_review_loop_traces.jsonl`

All proof commands exited 0 after copying the CLI default trace files into this run folder.

## Guard Behavior Observed

`demo_trace_repo_local.jsonl` contains real guard events:

- `guard.budget_warning` at cost used `$0.8400` against limit `$1.0000`
- `guard.budget_exceeded` at `$1.0800 > $1.0000`
- `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2

`coding_agent_review_loop_traces.jsonl` contains real coding-agent enforcement:

- `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3
- `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3

`doctor_trace_repo_local.jsonl` contains the local `doctor.verify` span.

## Artifacts

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
- SDK package: local and PyPI `agentguard47` are `1.2.10`.
- MCP package: local and npm `@agentguard47/mcp-server` are `0.2.2`.
- Latest GitHub tag observed: `v1.2.10`.
- GitHub release observed: `AgentGuard v1.2.10`.
- Official MCP Registry search still reports `0.2.1` for `io.github.bmdhodl/agentguard47`.
- Glama API returned 200 with env schema present and `0` indexed tools.
- Ops freshness remains stale by policy: roadmap 3 weeks old, architecture 4 weeks old, tracked by issue #473.

## Validation

Recorded after proof generation:

- JSON/JSONL artifact parsing passed.
- UTF-8/BOM/NUL/local-path hygiene passed.
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q` passed.
- `python scripts/sdk_release_guard.py --check-mcp-npm` passed.
- `git diff --check` passed.
