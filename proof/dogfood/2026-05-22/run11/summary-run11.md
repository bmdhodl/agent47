# AgentGuard Dogfood Proof - 2026-05-22 Run 11

## Scope

SDK-only dogfood run for the public AgentGuard47 repo. No dashboard, auth,
billing, secrets, deployment, or release work.

## Commands Run

- `python -m pip install -e .\sdk`
  - Attempted to rebind the editable install.
  - Windows denied rewriting the global `agentguard.exe`; repo binding was
    still forced with `PYTHONPATH=.\sdk`.
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts\sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Raw Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard-events-run11.json`
- `trace-inspection.txt`
- `agentguard-demo-report.txt`
- `coding-agent-review-loop-incident.txt`
- command output captures in this directory

## Guard Behavior Observed

AgentGuard enforcement was real and trace-backed.

- `agentguard_demo_traces.jsonl`
  - `guard.budget_warning`: 1
  - `guard.budget_exceeded`: 1
  - `guard.loop_detected`: 1
  - `guard.retry_limit_exceeded`: 1
  - Budget enforcement stopped at `$1.0800 > $1.0000`.
  - Loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
  - Retry enforcement stopped `fetch_docs` after 3 attempts with limit 2.
- `coding_agent_review_loop_traces.jsonl`
  - `guard.budget_exceeded`: 1
  - `guard.retry_limit_exceeded`: 1
  - Budget enforcement stopped the review loop on attempt 3 at
    `$0.0510 > $0.0450`.
  - Retry enforcement stopped `apply_patch` on attempt 4 with limit 3.

## Validation

- Focused dogfood tests: `35 passed in 1.43s`.
- Release guard: `Release guard passed.`
- `git diff --check`: passed.
- BOM scan for run11 text artifacts: none.

## Repo Health Notes

- Roadmap freshness: `2 weeks ago`.
- Architecture freshness: `3 weeks ago`.
- Docs freshness remains tracked by issue #473.
- GitHub release, PyPI, and local SDK version remain `1.2.10`.
- npm and local MCP package version remain `0.2.2`.
