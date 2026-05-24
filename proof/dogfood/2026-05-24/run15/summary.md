# Dogfood Run 15 - 2026-05-24

## Goal

Keep one real AgentGuard workflow running against this public SDK repo and leave durable proof that guards enforced real behavior.

## Scope

SDK-only proof artifact refresh. No dashboard, auth, billing, secrets, deployments, release, or paid-feature code was touched.

## Commands Run

- `python -m pip install -e ./sdk`
- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `gh pr list --state open --limit 100 --json ...`
- `gh issue list --state open --limit 100 --json ...`
- `gh release view --json tagName,name,publishedAt,url,isPrerelease,isDraft`
- `python -m pip index versions agentguard47`
- `npm view @agentguard47/mcp-server version`
- `gh api graphql` review-thread sweep for open PRs
- `Invoke-WebRequest https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47`
- `Invoke-WebRequest https://registry.modelcontextprotocol.io/v0/servers?search=agentguard47`

## Trace Artifacts

- `installed_doctor_trace.jsonl`
- `installed_demo_traces.jsonl`
- `repo_doctor_trace.jsonl`
- `repo_demo_traces.jsonl`
- `review_loop_traces.jsonl`
- `repo_demo_report.md`
- `repo_demo_incident.md`
- `review_loop_incident.md`
- `guard_events.json`
- `trace_inspection.txt`

## Concrete Guard Behavior Observed

Raw JSONL inspection found 94 trace records and 14 important doctor/guard events:

- `doctor.verify`: 4 span records across installed and repo-local doctor runs.
- `guard.budget_warning`: 2 events at USD 0.8400 / USD 1.0000.
- `guard.budget_exceeded`: 3 events.
  - Installed demo stopped at USD 1.0800 > USD 1.0000.
  - Repo-local demo stopped at USD 1.0800 > USD 1.0000.
  - Review-loop proof stopped at USD 0.0510 > USD 0.0450 on attempt 3.
- `guard.loop_detected`: 2 events for repeated `tool.search`.
- `guard.retry_limit_exceeded`: 3 events.
  - Installed and repo-local demo stopped `fetch_docs` attempt 3 with limit 2.
  - Review-loop proof stopped `apply_patch` attempt 4 with limit 3.

This counts as real dogfood proof because the run produced guard events and incident/report output showing enforcement, not just successful command execution.

## Repo Health Snapshot

- Open PRs: 25.
- Review sweep: 56 review threads across open PRs; 0 active unresolved non-outdated threads.
- PR #506 is the rolling proof PR. It was green before this run and still requires human review.
- PR #508 remains the concrete failing PR: setup-go Dependabot bump with Python CI failures/cancellations.
- PRs #509 and #510 are green but require review.
- Issue #473 remains the active stale-docs tracker. Current staleness: roadmap 2 weeks old; architecture 3 weeks old.
- Issue #507 and #469 remain security/dependency audit sinks; #418 remains the weekly drift bucket; #511 tracks the Claude-default-model docs audit.

## Release and Distribution Snapshot

- GitHub release: latest release metadata captured in `github_release.json`.
- PyPI: `agentguard47` latest and installed are 1.2.10. The `pip index` command emitted the standard experimental-command warning and exited nonzero under PowerShell native error handling, but the captured output shows latest 1.2.10.
- Local SDK: `sdk/pyproject.toml` version is 1.2.10.
- npm MCP: `@agentguard47/mcp-server` is 0.2.2.
- Local MCP metadata: `mcp-server/package.json` and `mcp-server/server.json` are 0.2.2.
- Glama and MCP Registry snapshots were captured for the current external-index state.

## Done Criteria

- In-repo proof artifact produced under `proof/dogfood/2026-05-24/run15/`.
- Raw installed and repo-local trace files saved.
- Guard events parsed into `guard_events.json` and summarized in `trace_inspection.txt`.
- Report and incident outputs saved.
- Repo health, release, distribution, PR, issue, and review-thread snapshots saved.
- Focused validation passed: 45 tests passed in 1.79s.
- `python scripts/sdk_release_guard.py --check-mcp-npm` passed.
- `git diff --check` passed with no output.
- Artifact hygiene passed: UTF-8, no BOM, no NUL bytes, JSON/JSONL parsed, and no exact local repo path leak.
- Final GitHub publication is recorded in PR/issue comments after push.
- Post-wait review sweep found 25 open PRs, 56 review threads, and 0 active unresolved non-outdated threads.
