# Dogfood Proof - 2026-05-28 run1

Host run time: 2026-05-27T21:46:21-05:00. Artifact date follows the UTC automation day.

## Goal

Keep a real AgentGuard workflow running against the public SDK checkout and leave durable proof that runtime guards enforced real stops.

## Scope

- Repo-local SDK proof through `PYTHONPATH=./sdk`
- Generated proof artifacts under `proof/dogfood/2026-05-28/run1/`
- Rolling GitHub dogfood issue update

## Non-goals

- No dashboard, auth, billing, secrets, deployment, paid-feature, or release work
- No SDK runtime changes
- No new dependencies

## Commands Run

- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run1/doctor-trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run1/demo-trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `Move-Item coding_agent_review_loop_traces.jsonl proof/dogfood/2026-05-28/run1/coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-28/run1/demo-trace.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-28/run1/demo-trace.jsonl --format markdown`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

The installed `agentguard` shim was present, but it resolved to another editable checkout. This run used the repo-local `PYTHONPATH=./sdk` path as canonical proof.

## Guard Events Observed

From `demo-trace.jsonl`:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

From `coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement was real:

- Demo stopped runaway spend after cost exceeded 1.00 USD.
- Demo stopped repeated `tool.search({"query":"python asyncio"})` calls.
- Demo stopped `fetch_docs` retry attempt 3 with limit 2.
- Review loop stopped at 0.0510 USD over the 0.0450 USD budget.
- Review loop stopped `apply_patch` retry attempt 4 with limit 3.

## Artifacts

- Raw doctor trace: `doctor-trace.jsonl`
- Raw demo trace: `demo-trace.jsonl`
- Raw coding-agent review-loop trace: `coding_agent_review_loop_traces.jsonl`
- Command output: `doctor-output.txt`, `demo-output.txt`, `review-loop-output.txt`
- Report and incident output: `report-output.txt`, `incident-output.md`
- Parsed proof: `guard_events.json`, `trace_inspection.txt`
- Repo health snapshots: `open-prs.json`, `open-issues.json`, `release_snapshot.md`

## Validation

- Focused proof pytest slice: 35 passed.
- MCP npm release guard: passed.
- Trace inspection confirmed demo and review-loop guard events.
- Artifact scan found no local worktree path leaks.

## Repo Health Notes

- Roadmap is about 3 weeks old and architecture is about 4 weeks old, stale by AGENTS.md thresholds. Issue #473 already tracks this.
- GitHub release and PyPI remain aligned at `v1.2.10` / `1.2.10`.
- npm MCP package remains aligned at `@agentguard47/mcp-server@0.2.2`.
- PR #531 is failing because `sdk/PYPI_README.md` is out of sync after README edits.
- The green proof/fix queue remains blocked by required human review.
