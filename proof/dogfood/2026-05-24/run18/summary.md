# AgentGuard dogfood proof - 2026-05-24 run18

## Scope

SDK-only recurring dogfood run against the public AgentGuard checkout. No runtime SDK, dashboard, auth, billing, deployment, dependency, or release changes were made.

## Commands run

- `python -m pip install -e ./sdk` to bind the package-installed import path to this checkout before counting installed CLI proof.
- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `gh pr list`, `gh issue list`, `gh release view`, `gh pr view 506`, `gh issue view 490`, and GraphQL review-thread sweep.

## Guard behavior observed

Real enforcement was observed in trace output.

- Installed demo emitted `guard.budget_warning` at USD 0.8400 / USD 1.0000.
- Installed demo emitted `guard.budget_exceeded` at USD 1.0800 > USD 1.0000.
- Installed demo emitted `guard.loop_detected` for repeated `tool.search` calls.
- Installed demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Repo-local demo emitted the same budget, loop, and retry guard events.
- Repo-local review-loop proof emitted `guard.budget_exceeded` at USD 0.0510 > USD 0.0450.
- Repo-local review-loop proof emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- Installed and repo-local doctor traces emitted `doctor.verify` start/end spans.

## Artifact files

- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `repo_coding_agent_review_loop_traces.jsonl`
- `repo_agentguard_report_demo.txt`
- `repo_agentguard_incident_review_loop.txt`
- `guard_events.json`
- `trace_inspection.txt`
- `validation_pytest.txt`
- `validation_release_guard.txt`
- `release_distribution_snapshot.txt`
- `open_prs_snapshot.json`
- `open_issues_snapshot.json`
- `review_thread_summary.json`

## Validation

- Focused proof/CLI/metadata tests: 35 passed in 1.62s.
- Release guard with MCP npm check: passed.
- Review-thread sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.
- Release/package alignment: GitHub release `v1.2.10`, PyPI `agentguard47` latest/installed `1.2.10`, npm MCP `0.2.2`, local MCP `0.2.2`.

## Repo health notes

- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old; issue #473 remains the existing freshness tracker.
- PR #506 remains the rolling dogfood proof PR and still needs human review.
- PR #508 still has failing/cancelled Python checks on the setup-go Dependabot bump.
- PRs #509 and #510 are green but still require review.
- New tech-debt issues #512 through #515 appear to be scanner noise from docs/proof artifacts and need triage rather than SDK runtime work.