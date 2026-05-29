# Dogfood run 12 - 2026-05-29

## Scope

Recurring AgentGuard dogfood proof for the public SDK repo. This run is SDK-only
and adds proof artifacts only.

## Commands run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

Repo-local import binding resolved to `<repo>\sdk\agentguard\__init__.py`.

`agentguard_demo_traces.raw.jsonl` emitted:

- `guard.budget_warning`
- `guard.budget_exceeded`: `Cost budget exceeded: $1.0800 > $1.0000`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

`coding_agent_review_loop_traces.raw.jsonl` emitted:

- `guard.budget_exceeded`: `Cost budget exceeded: $0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: `apply_patch` attempted 4 times with limit 3

Enforcement was real. The proof does not rely on stdout-only success.

## Artifacts

- `00_import_binding.txt`
- `01_path_agentguard_doctor.txt`
- `02_module_doctor.txt`
- `03_module_demo.txt`
- `04_review_loop.txt`
- `05_demo_report.txt`
- `06_demo_incident.txt`
- `07_review_loop_incident.txt`
- `08_focused_tests.txt`
- `09_release_guard_mcp_npm.txt`
- `agentguard_doctor_trace.raw.jsonl`
- `agentguard_demo_traces.raw.jsonl`
- `coding_agent_review_loop_traces.raw.jsonl`
- `trace_inspection.txt`

## Validation

- Focused proof/metadata tests passed: `35 passed in 1.37s`.
- MCP npm release guard passed.
- Roadmap freshness is stale at `3 weeks ago`.
- Architecture freshness is stale at `4 weeks ago`.

## Repo health

- GitHub latest release is `v1.2.10`, published `2026-05-02T15:48:03Z`.
- PyPI latest is `1.2.10`.
- Local SDK version is `1.2.10`.
- npm `@agentguard47/mcp-server` latest is `0.2.2`.
- Local MCP package and server metadata are `0.2.2`.
- Official MCP Registry still reports `io.github.bmdhodl/agentguard47` at `0.2.1`.
- Glama API returned HTTP 403 from this environment.

## GitHub artifact

This run updates rolling dogfood PR `#544` and rolling dogfood issue `#490`.
