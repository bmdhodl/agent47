# AgentGuard Dogfood Proof - 2026-05-24 run17

## Scope

SDK-only recurring dogfood pass for the public AgentGuard47 repo. No dashboard, auth, billing, secrets, deployments, paid-feature, or release work.

## Commands run

- `agentguard doctor`
- `agentguard demo`
- `python -m pip install -e ./sdk` to rebind the editable install from an older worktree to this checkout
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `gh pr list`, `gh issue list`, `gh pr view 506 --comments`, `gh issue view 490 --comments`, `gh pr checks 506`, and PR review-thread GraphQL snapshot
- `gh release view`, `python -m pip index versions agentguard47`, `npm view @agentguard47/mcp-server version`, `npm view @agentguard47/mcp-server dist-tags --json`

## Guard behavior observed

Trace inspection is saved in `trace_inspection.txt` and parsed events are saved in `guard_events.json`.

- `repo_agentguard_doctor_trace.jsonl`: `doctor.verify` start/end spans observed.
- `repo_agentguard_demo_traces.jsonl`: `guard.budget_warning` at USD 0.8400 / USD 1.0000.
- `repo_agentguard_demo_traces.jsonl`: `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- `repo_agentguard_demo_traces.jsonl`: `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- `repo_agentguard_demo_traces.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at USD 0.0510 > USD 0.0450 on review attempt 3.
- `coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

Enforcement was real. The proof is trace-backed and not based on exit codes alone.

## Outputs saved

- Raw installed CLI traces: `installed_agentguard_doctor_trace.jsonl`, `installed_agentguard_demo_traces.jsonl`
- Raw repo-local traces: `repo_agentguard_doctor_trace.jsonl`, `repo_agentguard_demo_traces.jsonl`, `coding_agent_review_loop_traces.jsonl`
- Reports/incidents: `repo_demo_report.txt`, `review_loop_incident.txt`
- Parsed proof: `guard_events.json`, `trace_inspection.txt`, `trace_parse_output.txt`
- Validation: `pytest_focused.txt`, `release_guard_check_mcp_npm.txt`
- Live repo/package snapshots: `open_prs.json`, `open_issues.json`, `pr_506_snapshot.json`, `issue_490_snapshot.json`, `pr_506_review_threads.json`, `pr_506_checks.txt`, `github_release.json`, `pypi_agentguard47_versions.txt`, `npm_mcp_version.txt`, `npm_mcp_dist_tags.json`
- Post-wait review artifacts: `pr_506_post_wait_snapshot.json`, `pr_506_post_wait_review_threads.json`, `review_thread_summary.txt`, `review_thread_parse_output.txt`

## Repo health notes

- Roadmap staleness: `roadmap_staleness.txt` reports 2 weeks old.
- Architecture staleness: `architecture_staleness.txt` reports 3 weeks old.
- GitHub release remains `v1.2.10`.
- PyPI latest remains `agentguard47==1.2.10`.
- npm latest remains `@agentguard47/mcp-server@0.2.2`.
- PR #506 checks were green at snapshot time and review remains required.
- Post-wait review sweep found 0 active unresolved non-outdated threads.
- PR #508 still has failing/cancelled Python checks.
- PRs #509 and #510 remain green but need human review.

## Validation result

- Focused proof tests: 35 passed.
- Release guard with MCP npm check: passed.