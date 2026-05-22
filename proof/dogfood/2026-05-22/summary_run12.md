# AgentGuard dogfood proof - 2026-05-22 run12

## Scope

- Repo: bmdhodl/agent47 public SDK repo.
- Branch/PR: codex/dogfood-proof-2026-05-22-run8-fix, PR #502.
- SDK-only proof run. No dashboard, auth, billing, secrets, deployment, or release work.
- Roadmap/architecture freshness warning remains active: roadmap is 2 weeks old, architecture is 3 weeks old.

## Commands run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Guard behavior observed

Demo trace emitted all expected offline enforcement events:

- `guard.budget_warning`: cost used `0.84` against limit `1.00`.
- `guard.budget_exceeded`: cost used `1.08` exceeded limit `1.00`.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the 6-call window.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2.

Coding-agent review-loop trace emitted real stop behavior:

- `guard.budget_exceeded`: review attempt 3 stopped at `$0.0510 > $0.0450` after adding `$0.0205`.
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 stopped with retry limit 3.

This counts as real dogfood proof because the raw trace files contain guard events and the incident output classifies the review-loop trace as an incident.

## Files in this proof bundle

- `repo_import_run12.txt`
- `agentguard_doctor_output_run12.txt`
- `module_doctor_output_run12.txt`
- `agentguard_doctor_trace_run12.jsonl`
- `agentguard_demo_output_run12.txt`
- `agentguard_demo_traces_run12.jsonl`
- `agentguard_demo_report_run12.txt`
- `coding_agent_review_loop_output_run12.txt`
- `coding_agent_review_loop_traces_run12.jsonl`
- `coding_agent_review_loop_incident_run12.md`
- `guard_events_run12.json`
- `focused_tests_run12.txt`
- `release_guard_run12.txt`
- `git_diff_check_run12.txt`
- `artifact_scan_run12.txt`

## Validation

- Focused proof tests: 35 passed.
- Release guard with MCP npm check: passed.
- `git diff --check`: clean.
- Proof artifact scan: UTF-8 without BOM/NUL bytes and no local absolute paths.

## Repo health notes

- Release/package alignment verified: GitHub release `v1.2.10`, PyPI `agentguard47==1.2.10`, npm `@agentguard47/mcp-server==0.2.2`, local SDK `1.2.10`, local MCP metadata `0.2.2`.
- Glama still returns an empty `tools` array from the public API.
- Official MCP Registry search still reports `@agentguard47/mcp-server@0.2.1`.
- PRs remain green but review-blocked; no merge was available without human approval.