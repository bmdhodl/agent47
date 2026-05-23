# AgentGuard Dogfood Proof - 2026-05-23 run16

## Scope
- SDK-only dogfood run for the public AgentGuard repo.
- No dashboard, auth, billing, secrets, deployments, paid features, dependencies, or releases touched.
- Existing rolling sinks reused: PR #506 and issue #490.

## Commands run
- `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `agentguard demo`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

The run produced real guard events in JSONL traces, not just successful process exits.
- `agentguard_demo_traces.jsonl`
  - `guard.budget_warning`: cost used `$0.84` of `$1.00`
  - `guard.budget_exceeded`: `$1.0800 > $1.0000`
  - `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})`
  - `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2
- `python_module_demo_traces.jsonl`
  - Same budget, loop, and retry enforcement as the installed CLI demo path.
- `coding_agent_review_loop_traces.jsonl`
  - `guard.budget_exceeded`: review attempt 3 stopped at `$0.0510 > $0.0450`
  - `guard.retry_limit_exceeded`: `apply_patch` attempt 4 stopped with limit 3

## Validation
- Focused SDK proof tests: `35 passed in 1.47s`
- Release guard: `Release guard passed.`
- Roadmap staleness: `2 weeks ago`
- Architecture staleness: `3 weeks ago`
- PR review-thread sweep: 25 open PRs, 0 active unresolved non-outdated threads.

## Release and distribution snapshot
- GitHub latest release: `v1.2.10`, published 2026-05-02.
- PyPI latest: `agentguard47 1.2.10`.
- npm latest: `@agentguard47/mcp-server 0.2.2`.
- Local MCP metadata: `mcp-server/package.json` and `mcp-server/server.json` are `0.2.2`.
- Official MCP Registry still reports `io.github.bmdhodl/agentguard47` / `@agentguard47/mcp-server` at `0.2.1`.
- Glama API still reports `tools: []`.

## Files in this bundle
- `agentguard_doctor_trace.jsonl`
- `python_module_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `python_module_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.txt`
- `demo_incident.md`
- `review_loop_report.txt`
- `review_loop_incident.md`
- `guard_events.json`
- `focused_tests.txt`
- `release_guard.txt`
- `open_prs.json`
- `open_issues.json`
- `review_threads.json`
- `review_thread_summary.json`
- `github_release.json`
- `pypi_versions.txt`
- `npm_mcp_version.txt`
- `local_mcp_versions.txt`
- `mcp_registry_search.json`
- `glama_api.json`

