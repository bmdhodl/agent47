# Dogfood proof - 2026-05-27 run1

## Scope

SDK-only recurring dogfood run appended to PR #516 from its existing proof branch.

No dashboard, auth, billing, secret, deployment, paid-feature, or runtime SDK code was changed.

## Commands

Proof commands:

- `python -m pip install -e ./sdk`
- `agentguard doctor --trace-file installed_agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file installed_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file repo_agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli report repo_coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident repo_coding_agent_review_loop_traces.jsonl`

All proof commands exited `0`; see `command-status.txt` and `command-status.json`.

## Guard behavior observed

Installed and repo-local `doctor` emitted `doctor.verify` spans.

Installed and repo-local `demo` emitted these guard events:

- `guard.budget_warning`: demo reached the configured warning threshold at USD 0.8400 of a USD 1.0000 limit.
- `guard.budget_exceeded`: demo crossed the configured cost cap at USD 1.0800 > USD 1.0000.
- `guard.loop_detected`: repeated `tool.search` calls were stopped.
- `guard.retry_limit_exceeded`: `fetch_docs` attempt 3 exceeded the retry ceiling of 2.

Repo-local `examples/coding_agent_review_loop.py` emitted:

- `guard.budget_exceeded`: review loop stopped at USD 0.0510 > USD 0.0450.
- `guard.retry_limit_exceeded`: `apply_patch` stopped on attempt 4 with limit 3.

Enforcement was real. The trace files contain AgentGuard guard events and the stdout captures show the demo and review-loop work stopped at configured limits.

## Raw artifacts

- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `repo_coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `repo-demo-report.stdout.txt`
- `repo-demo-incident.stdout.txt`
- `repo-review-loop-report.stdout.txt`
- `repo-review-loop-incident.stdout.txt`
- `open-prs.stdout.txt`
- `open-issues.stdout.txt`
- `github-release.stdout.txt`
- `pypi-agentguard47.stdout.txt`
- `npm-mcp-server.stdout.txt`
- `glama-agent47.stdout.txt`
- `mcp-registry-agentguard-search.stdout.txt`

## Validation

- Focused CLI/report/demo/doctor/quickstart/metadata tests: `============================= 48 passed in 1.08s ==============================`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Artifact JSONL parse and guard-event extraction: passed.

## Repo health snapshot

- PR #516 is green but review-required, and this run appends fresh proof there.
- PR #508 still has failed/cancelled Python checks from the setup-go Dependabot bump.
- PRs #509 and #510 are green but review-required.
- Issue #473 still tracks stale ops docs; local staleness check reports roadmap 3 weeks old and architecture 4 weeks old.
- GitHub release and PyPI remain aligned at SDK `v1.2.10`; local MCP metadata remains `0.2.2`.
- Known external drift remains: MCP Registry search reports `0.2.1`; Glama still needs tool indexing recheck/action.

## Next action

Fix or close PR #508 by updating the CI guardrail expectation for pinned `actions/setup-go@v6.4.0`, then rerun CI.
