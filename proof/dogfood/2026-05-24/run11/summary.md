# AgentGuard Dogfood Proof - 2026-05-24 run11

## Scope

SDK-only recurring dogfood run for the public AgentGuard repo. No dashboard,
auth, billing, secrets, deployment, paid-feature, or release work was touched.

## Commands Run

- `agentguard doctor --trace-file proof/dogfood/2026-05-24/run11/installed_agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-24/run11/installed_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run11/repo_agentguard_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run11/repo_agentguard_demo_traces.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run11/repo_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run11/repo_agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-24/run11/repo_coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-24/run11/repo_coding_agent_review_loop_traces.jsonl`

All proof commands exited `0`; see `command_exit_codes.json`.

## Guard Behavior Observed

Raw trace evidence is preserved in:

- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `repo_coding_agent_review_loop_traces.jsonl`

Concrete events parsed from those traces:

- Installed and repo-local doctor emitted `doctor.verify` start/end events.
- Installed and repo-local demo emitted `guard.budget_warning` at `$0.8400 / $1.0000`.
- Installed and repo-local demo emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Installed and repo-local demo emitted `guard.loop_detected` for repeated `tool.search`.
- Installed and repo-local demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- The coding-agent review-loop proof emitted `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- The coding-agent review-loop proof emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

This run counts as real enforcement proof because guard events and command
stdout both show AgentGuard stopping budget, loop, and retry failure modes.

## Derived Outputs

- `guard_events.json` - parsed guard and doctor events.
- `trace_inspection.json` - per-trace event counts and parsed evidence.
- `trace_inspection.txt` - human-readable trace inspection.
- `repo_demo_report.txt` and `repo_demo_incident.md` - report/incident output for the demo trace.
- `repo_review_loop_report.txt` and `repo_review_loop_incident.md` - report/incident output for the coding-agent review-loop trace.

## Validation

- Focused proof/CLI/metadata tests: `36 passed in 0.73s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Review-thread sweep before push: PR #506 has 0 active unresolved non-outdated threads.
- Post-wait PR #506 checks: CI and CodeQL passed; 0 active unresolved non-outdated threads.

## Repo Health Snapshot

- PR #506 is still the consolidated rolling proof PR.
- PR #508 still fails CI from the setup-go Dependabot bump guardrail expectation.
- PRs #509 and #510 are green but require human review.
- Issues #507 and #469 remain security/dependency audit sinks; issue #473 tracks stale roadmap/architecture docs.
- Freshness warning remains: `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old.

## Release and Distribution Snapshot

- GitHub release: `v1.2.10`.
- PyPI `agentguard47`: latest and installed version `1.2.10`.
- Local SDK metadata: `sdk/pyproject.toml` version `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Local MCP metadata: `mcp-server/package.json` and `mcp-server/server.json` version `0.2.2`.
- Official MCP Registry search still reports package metadata `0.2.1`.
- Glama API is reachable but still reports 0 indexed tools.

## Next Action

Highest-ROI next task remains distribution hygiene: refresh official MCP
Registry metadata to `0.2.2`, then recheck Glama tool indexing before updating
the `awesome-mcp-servers` PR.
