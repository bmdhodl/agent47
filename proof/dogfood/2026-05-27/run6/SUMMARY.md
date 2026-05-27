# AgentGuard Dogfood Run 6 - 2026-05-27

## Scope

- Repo: `bmdhodl/agent47`
- Checkout commit: `3f54935`
- Branch state: detached HEAD before proof branch creation
- SDK-only run. No dashboard, auth, billing, secrets, deployment, or release work.

## Commands Run

- `agentguard doctor --trace-file agentguard_installed_doctor_trace.jsonl`
- `agentguard demo --trace-file agentguard_installed_demo_traces.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 agentguard doctor --trace-file agentguard_doctor_trace.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 python examples/coding_agent_review_loop.py`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `py -3.10 -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `git diff --check`

## Guard Behavior Observed

Direct trace inspection confirmed real guard behavior:

- `agentguard_demo_traces.jsonl`: 36 events
  - `guard.budget_warning`: 1
  - `guard.budget_exceeded`: 1
  - `guard.loop_detected`: 1
  - `guard.retry_limit_exceeded`: 1
- `coding_agent_review_loop_traces.jsonl`: 14 events
  - `guard.budget_exceeded`: 1
  - `guard.retry_limit_exceeded`: 1
- `agentguard_doctor_trace.jsonl`: 4 events
  - no guard stop expected; doctor verifies local trace writing.

Enforcement was real. The demo stopped budget overrun, repeated tool calls, and retry storms. The coding-agent review loop stopped an over-budget review attempt and an `apply_patch` retry storm.

## Environment Notes

- Clean installed `agentguard` still resolves through a stale editable checkout and corrupt Python 3.13 user-site metadata, so clean installed `doctor` and `demo` failed before CLI startup.
- Checkout-bound proof succeeded with `PYTHONPATH=sdk` and `PYTHONNOUSERSITE=1`; `agentguard.__file__` resolved to this worktree.
- PyPI latest is `agentguard47 1.2.10`.
- npm latest is `@agentguard47/mcp-server 0.2.2`.
- GitHub latest release is `v1.2.10`.
- Roadmap is 3 weeks old and architecture is 4 weeks old; issue #473 already tracks ops-doc freshness.

## Validation

- Focused proof pytest: 35 passed.
- `git diff --check`: passed.
- Parsed guard-event validation: passed.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `demo-report.log`
- `review-incident.log`
- command logs for installed and checkout-bound proof commands
- `focused-pytest.log`
- `git-diff-check.log`
