# AgentGuard Dogfood Proof - 2026-05-22 Run 13

## Scope

- SDK-only dogfood run from the public AgentGuard repo.
- No dashboard, secrets, billing, deployments, releases, or paid-feature code touched.
- Local SDK binding was pinned with `PYTHONPATH=./sdk`.

## Commands Run

- `python -m pip install -e ./sdk`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_example_starters.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`
- `python -m pip index versions agentguard47`
- `npm view @agentguard47/mcp-server version`
- `gh release view --json tagName,publishedAt,url`

## Guard Behavior Observed

Raw trace inspection confirmed real enforcement, not stdout-only success.

Demo trace:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1, stopped at `$1.0800 > $1.0000`
- `guard.loop_detected`: 1, stopped repeated `tool.search`
- `guard.retry_limit_exceeded`: 1, stopped `fetch_docs` retry storm

Coding-agent review-loop trace:

- `guard.budget_exceeded`: 1, stopped at `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: 1, stopped `apply_patch` attempt 4 with limit 3

## Notes

- The installed CLI executable worked after pinning `PYTHONPATH`, but `pip install -e ./sdk` logged a Windows access-denied warning while replacing `agentguard.exe`. The repo-local import still resolved correctly, and both CLI forms executed successfully.
- This branch still reproduces the known review-loop incident cost-reporting drift: enforcement stopped at `$0.0510 > $0.0450`, while the incident report estimated `$0.1020`. PR #502 already carries the code fix for that issue, so this proof-only update does not duplicate it.

## Artifacts

- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `trace-inspection.txt`
- `demo-report.txt`
- `review-loop-incident.txt`
- `focused-tests.txt`
- `release-guard.txt`
- `artifact-scan.txt`

## Validation

- Focused SDK proof tests: `35 passed in 1.73s`
- Release guard: passed
- `git diff --check`: passed
- Artifact UTF-8/BOM/NUL/local-path scan: passed

