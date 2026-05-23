# Dogfood operator run 10 - 2026-05-23

## Commands run

- `where.exe agentguard`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `agentguard demo`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

The checkout-bound proof used `PYTHONPATH=./sdk` and confirmed the import resolved to this checkout.

`agentguard_demo_traces.jsonl` emitted:

- `guard.budget_warning`
- `guard.budget_exceeded` at `$1.0800 > $1.0000`
- `guard.loop_detected` for repeated `tool.search`
- `guard.retry_limit_exceeded` for `fetch_docs`

`coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3
- `guard.retry_limit_exceeded` for `apply_patch` attempt 4

Enforcement was real. This run does not count stdout-only success as proof; the guard events above were extracted from the raw JSONL traces and saved in `guard_events.json`.

## Artifacts

- `proof/dogfood/2026-05-23/run10/agentguard_demo_traces.jsonl`
- `proof/dogfood/2026-05-23/run10/coding_agent_review_loop_traces.jsonl`
- `proof/dogfood/2026-05-23/run10/installed_agentguard_demo_traces.jsonl`
- `proof/dogfood/2026-05-23/run10/installed_agentguard_doctor_trace.jsonl`
- `proof/dogfood/2026-05-23/run10/repo_agentguard_doctor_trace.jsonl`
- `proof/dogfood/2026-05-23/run10/guard_events.json`
- `proof/dogfood/2026-05-23/run10/demo-report.txt`
- `proof/dogfood/2026-05-23/run10/demo-incident.txt`
- `proof/dogfood/2026-05-23/run10/review-incident.txt`
- `proof/dogfood/2026-05-23/run10/command-output.txt`
- `proof/dogfood/2026-05-23/run10/validation-output.txt`
- `proof/dogfood/2026-05-23/run10/release-distribution-snapshot.txt`
- `proof/dogfood/2026-05-23/run10/repo-health-snapshot.txt`
- `proof/dogfood/2026-05-23/run10/pr-506-review-state.json`
- `proof/dogfood/2026-05-23/run10/open-pr-review-thread-sweep.json`

## Validation

- Focused proof tests: `35 passed in 2.43s`
- Release guard: `Release guard passed.`

## Repo health notes

- Freshness warning remains: `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old and `ops/02-ARCHITECTURE.md` is 3 weeks old.
- GitHub release, PyPI, and local SDK metadata align at `1.2.10`.
- npm and local MCP metadata align at `0.2.2`.
- Official MCP Registry still reports `0.2.1`.
- Glama API still returns an empty `tools` array.
- PR #506 was green before this commit and still `REVIEW_REQUIRED`.
- The pre-push open-PR review-thread sweep found 0 active unresolved non-outdated threads across 25 open PRs.
- PR #508 still has failing CI from the setup-go Dependabot bump and needs the guardrail expectation updated or the Dependabot branch refreshed.
