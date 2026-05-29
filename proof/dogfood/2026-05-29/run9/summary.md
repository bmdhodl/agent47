# Dogfood Run 9 - 2026-05-29

## Scope

SDK-only recurring dogfood run from the active AgentGuard checkout. No dashboard, auth, billing, deployment, secret, or paid-feature code was touched.

## Commands Run

- `python -m pip install -e ./sdk`
- `agentguard doctor --json`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --json`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard Behavior Observed

Raw traces are saved in this folder.

- `agentguard_doctor_trace.jsonl`: emitted `doctor.verify` start and end events.
- `agentguard_demo_traces.jsonl`: emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement was real: `Cost budget exceeded: $1.0800 > $1.0000`.
- Demo loop enforcement was real: `tool.search({"query":"python asyncio"})` repeated 3 times.
- Demo retry enforcement was real: `fetch_docs` attempted 3 times with limit 2.
- `coding_agent_review_loop_traces.jsonl`: emitted `guard.budget_exceeded` and `guard.retry_limit_exceeded`.
- Review-loop budget enforcement was real: `$0.0510 > $0.0450` on attempt 3.
- Review-loop retry enforcement was real: `apply_patch` attempted 4 times with limit 3.

## Validation

- Focused proof tests passed: `35 passed`.
- Release guard passed.
- `git diff --check` passed.
- Artifact hygiene passed: UTF-8, no BOM/NUL, JSON/JSONL parse, and local path scrub.

## Repo Health Notes

- PR #544 is the active dogfood proof PR and remains blocked only by required human review.
- Roadmap and architecture freshness remain stale by repo policy: `3 weeks ago` and `4 weeks ago`.
- Issue #473 remains the right tracker for the ops-doc freshness pass.
- GitHub release and PyPI latest SDK remain `1.2.10`; npm MCP package remains `0.2.2`.
- Official MCP Registry metadata and Glama tool indexing remain external distribution follow-ups.

## Artifacts

- `command_status.json`
- `guard_events.json`
- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.out.txt`
- `review_loop_incident.out.txt`
- `focused_pytest.out.txt`
- `release_guard.out.txt`
- `release_distribution.out.txt`
- `staleness.out.txt`
- `artifact_hygiene.out.txt`
