# Dogfood Operator Run 15 - 2026-05-22

## Scope

- Repo: `bmdhodl/agent47`
- Checkout binding: `PYTHONPATH=./sdk`
- Goal: prove AgentGuard still enforces local runtime guards on its own repo workflow.
- Non-goals: no release, no dashboard work, no paid-feature work, no new runtime dependency.

## Commands Run

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

## Guard Behavior Observed

AgentGuard enforcement was real and trace-backed.

- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `trace-inspection.txt`
- `demo-report.txt`
- `review-loop-incident.txt`
- `focused-tests.txt`
- `release-guard.txt`
- `git-diff-check.txt`
- `artifact-scan.txt`
- `pr-506-review-state.json`

## Validation

- Focused SDK proof tests: 35 passed in 1.53s.
- Release guard with npm metadata check: passed.
- `git diff --check`: passed.
- Artifact scan: passed, UTF-8 without BOM/NUL bytes and no local Windows user paths.
- PR #506 review-thread sweep: 0 active unresolved threads; merge remains blocked only on required review.

## Notes

- The proof-only branch still shows the known review-loop incident estimated-cost drift: incident output reports `$0.1020` while enforcement stopped at `$0.0510`.
- PR #502 already carries the code fix for that cost-accounting issue and remains review-blocked.
- This run appended proof to the existing dogfood PR #506 instead of opening another duplicate proof-only PR.
