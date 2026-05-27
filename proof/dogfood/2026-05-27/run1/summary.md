# AgentGuard Dogfood Proof - 2026-05-27 run1

## Scope

- Repo: `bmdhodl/agent47`
- Commit tested: `a2d9cce2fa8096d469fafcc8a4de1dac056d3166`
- Branch carrying this proof: `dogfood-2026-05-27-run1-worker`
- SDK-only run. No dashboard, auth, billing, secret, deployment, or release work.

## Commands run

All command stdout/stderr and exit codes are saved in this directory. See
`command-status.txt` for the full command ledger.

- `python -m pip install -e .\sdk`
- `agentguard doctor --trace-file ...\installed_agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file ...\installed_agentguard_demo_traces.jsonl`
- `agentguard report ...\installed_agentguard_demo_traces.jsonl`
- `agentguard incident ...\installed_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli doctor --trace-file ...\repo_agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file ...\repo_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report ...\repo_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident ...\repo_agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report ...\coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident ...\coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_reporting.py -q`
- `gh pr list`, `gh issue list`, `gh release view`, and focused PR review snapshots for #517 and #508

## Guard behavior observed

This run counts as real dogfood proof because the traces include guard
enforcement events, not just successful command exits.

- Installed CLI demo trace:
  - `guard.budget_warning`
  - `guard.budget_exceeded`
  - `guard.loop_detected`
  - `guard.retry_limit_exceeded`
- Repo-local CLI demo trace:
  - `guard.budget_warning`
  - `guard.budget_exceeded`
  - `guard.loop_detected`
  - `guard.retry_limit_exceeded`
- Coding-agent review-loop trace:
  - `guard.budget_exceeded`
  - `guard.retry_limit_exceeded`

The extracted event ledger is saved as `guard_events.json`.

## Report and incident artifacts

- Installed demo:
  - `installed_agentguard_demo_traces.jsonl`
  - `installed-demo-report.stdout.txt`
  - `installed-demo-incident.stdout.txt`
- Repo-local demo:
  - `repo_agentguard_demo_traces.jsonl`
  - `repo-demo-report.stdout.txt`
  - `repo-demo-incident.stdout.txt`
- Coding-agent review loop:
  - `coding_agent_review_loop_traces.jsonl`
  - `repo-review-loop-report.stdout.txt`
  - `repo-review-loop-incident.stdout.txt`

## Repo health observed

- GitHub release: `v1.2.10`
- PyPI package: `agentguard47==1.2.10`
- npm MCP package: `@agentguard47/mcp-server@0.2.2`
- MCP Registry search still reports package version `0.2.1`.
- Glama API snapshot returned `HTTP 403 Forbidden` from this environment.
- Roadmap staleness check: `ops/03-ROADMAP_NOW_NEXT_LATER.md` last changed 3 weeks ago.
- Architecture staleness check: `ops/02-ARCHITECTURE.md` last changed 4 weeks ago.
- Existing docs freshness tracker #473 already covers the stale ops-doc issue.
- PR #517 is green but review-required.
- PR #508 remains blocked by the setup-go guardrail expectation mismatch.

## Validation

- Focused local tests: 29 passed.
- All proof commands in `command-status.txt` exited 0.
- No SDK runtime code changed.

## Docs updates needed

No docs updates were made in this run. The stale ops docs should be handled
through the existing docs freshness tracker instead of mixed into this proof PR.
