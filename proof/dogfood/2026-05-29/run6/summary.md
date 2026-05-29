# AgentGuard Dogfood Run 6 - 2026-05-29

## Scope

SDK-only dogfood proof run for the public AgentGuard47 repo. No SDK behavior,
dashboard, auth, billing, deployment, dependency, or release changes were made.

## Commands Run

- `agentguard --help`
- `agentguard doctor --help`
- `agentguard demo --help`
- `agentguard doctor --json`
- `agentguard demo`
- `set PYTHONPATH=./sdk&& python -c "import agentguard; ..."`
- `set PYTHONPATH=./sdk&& python -m agentguard.cli doctor --json`
- `set PYTHONPATH=./sdk&& python -m agentguard.cli demo`
- `set PYTHONPATH=./sdk&& python examples/coding_agent_review_loop.py`
- `set PYTHONPATH=./sdk&& python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `set PYTHONPATH=./sdk&& python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `set PYTHONPATH=./sdk&& python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard Behavior Observed

This run counts as real dogfood proof because enforcement appeared in raw
AgentGuard JSONL traces, not only in command output.

- Installed and repo-local demo traces emitted `guard.budget_warning`.
- Installed and repo-local demo traces emitted `guard.budget_exceeded` at
  `$1.0800 > $1.0000`.
- Installed and repo-local demo traces emitted `guard.loop_detected` for
  repeated `tool.search({"query":"python asyncio"})`.
- Installed and repo-local demo traces emitted `guard.retry_limit_exceeded` for
  `fetch_docs` at attempt 3 with limit 2.
- The coding-agent review-loop trace emitted `guard.budget_exceeded` at
  `$0.0510 > $0.0450` on attempt 3.
- The coding-agent review-loop trace emitted `guard.retry_limit_exceeded` for
  `apply_patch` on attempt 4 with limit 3.

See `guard_events.json` for the extracted event data and the raw `*.jsonl`
files for complete trace evidence.

## Artifact Files

- Raw doctor traces: `doctor_trace.jsonl`, `doctor_trace_repo_local.jsonl`
- Raw demo traces: `demo_trace.jsonl`, `demo_trace_repo_local.jsonl`
- Raw review-loop trace: `coding_agent_review_loop_traces.jsonl`
- Reports: `demo_report.txt`, `review_loop_report.txt`
- Incident output: `review_loop_incident.md`
- Command evidence: `command_status.txt`
- Extracted guard events: `guard_events.json`
- Repo binding: `import_binding.txt`
- Release/distribution evidence: `github_release.json`, `pypi_versions.txt`,
  `npm_mcp_version.json`, `official_mcp_registry.json`, `glama.json`
- Validation evidence: `pytest_focused.txt`, `release_guard.txt`,
  `git_diff_check.txt`, `validation_status.txt`, `artifact_hygiene.txt`

## Validation

- Focused proof and metadata tests passed: `35 passed in 1.57s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm` passed.
- `git diff --check` passed.
- Artifact JSON/JSONL parse, UTF-8, BOM, NUL, and local-path hygiene passed.

## Repo Health Snapshot

- Repo identity: `https://github.com/bmdhodl/agent47.git`.
- Ops freshness warning remains: roadmap is 3 weeks old, architecture is 4
  weeks old. Existing issue #473 tracks this.
- Latest GitHub release is `v1.2.10`; PyPI latest and installed package are
  `1.2.10`.
- npm latest for `@agentguard47/mcp-server` is `0.2.2`, matching local MCP
  metadata.
- Official MCP Registry still reports `0.2.1`; Glama still returns `tools: []`.

## GitHub Artifact Target

This run should update the existing dogfood proof PR #544 and rolling issue
#490 rather than creating a duplicate dogfood PR.
