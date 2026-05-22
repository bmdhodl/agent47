# AgentGuard Dogfood Proof - 2026-05-22 run9

## Scope

- Branch: `codex/dogfood-proof-2026-05-22-run8-fix`
- Base purpose: refresh the existing dogfood proof/fix PR with a new operator run.
- Runtime binding: repo-local SDK import verified as `sdk/agentguard/__init__.py`.
- Dashboard, secrets, billing, deployment, and release flows were not touched.

## Commands Run

- `python -m pip install -e ./sdk`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_example_starters.py::test_coding_agent_review_loop_example_runs_offline sdk/tests/test_example_starters.py::test_coding_agent_review_loop_sample_incident_is_in_sync -q`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard Behavior Observed

AgentGuard enforcement was real. The proof is based on raw trace events, not stdout alone.

`agentguard_demo_traces.jsonl` emitted:

- `guard.budget_warning`: warning threshold reached at `$0.84` of `$1.00`.
- `guard.budget_exceeded`: hard stop at `$1.0800 > $1.0000`.
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})` stopped after 3 repeats.
- `guard.retry_limit_exceeded`: `fetch_docs` stopped at attempt 3 with limit 2.

`coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded`: review loop stopped at `$0.0510 > $0.0450` on attempt 3.
- `guard.retry_limit_exceeded`: `apply_patch` retry storm stopped on attempt 4 with limit 3.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard-doctor.txt`
- `python-doctor.txt`
- `agentguard-demo.txt`
- `coding-agent-review-loop.txt`
- `demo-report.txt`
- `demo-incident.txt`
- `review-loop-incident.txt`
- `trace-event-inspection.txt`
- `guard-events-run9.json`
- `focused-tests.txt`

## Validation

- Review-loop focused tests: `2 passed`.
- Dogfood focused slice: `35 passed`.
- Release guard with npm metadata check: passed.
- `git diff --check`: passed.

## Result

This run refreshed the dogfood proof on the existing PR branch that fixes review-loop incident cost accounting. The review-loop incident now reports `Estimated cost: $0.0510`, matching the actual guarded review attempts.
