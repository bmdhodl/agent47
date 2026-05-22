# Dogfood Proof - 2026-05-22

## Scope

- Repo: `bmdhodl/agent47`
- Checkout: `C:\Users\<USER>\.codex\worktrees\2b38\agent47`
- SDK-only local proof. No dashboard, auth, billing, secrets, deployments, or paid-feature code touched.
- Repo-bound import: `C:\Users\<USER>\.codex\worktrees\2b38\agent47\sdk\agentguard\__init__.py`

## Commands Run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard Behavior Observed

- `agentguard_doctor_trace.jsonl`: 4 total events
  - no guard events expected for this setup trace
- `agentguard_demo_traces.jsonl`: 36 total events
  - `guard.budget_exceeded`: 1
  - `guard.budget_warning`: 1
  - `guard.loop_detected`: 1
  - `guard.retry_limit_exceeded`: 1
- `coding_agent_review_loop_traces.jsonl`: 14 total events
  - `guard.budget_exceeded`: 1
  - `guard.retry_limit_exceeded`: 1

Concrete enforcement confirmed:

- `agentguard_demo_traces.jsonl` recorded `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- `coding_agent_review_loop_traces.jsonl` recorded `guard.budget_exceeded` at `$0.0510 > $0.0450` and `guard.retry_limit_exceeded` for `apply_patch` attempt 4.
- The review-loop incident report now reports `Estimated cost: $0.0510`, matching the three review iterations instead of double-counting the guard event.
- Enforcement was real: the demo and review-loop commands stopped budget, loop, and retry paths from continuing instead of only printing a status line.

## Validation

- Focused proof/distribution tests: `35 passed in 1.65s` before the review-fix patch; rerun after patch is recorded in the PR validation.
- Release guard: `Release guard passed.`

## Raw Artifacts

- `agentguard_demo_traces.jsonl`
- `agentguard_doctor.txt`
- `agentguard_doctor_trace.jsonl`
- `coding_agent_review_loop.txt`
- `coding_agent_review_loop_traces.jsonl`
- `demo.txt`
- `demo_report.txt`
- `import_binding.txt`
- `python_module_doctor.txt`
- `review_loop_incident.md`
- `summary.md`
