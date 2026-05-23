# Dogfood operator run 6 - 2026-05-23

## Scope

Recurring AgentGuard dogfood operator run for the public SDK repo. This run stayed SDK-only and updated the existing rolling proof PR.

## Commands run

- `git fetch origin codex/dogfood-proof-2026-05-22-run11`
- `git checkout codex/dogfood-proof-2026-05-22-run11`
- `git merge --ff-only origin/codex/dogfood-proof-2026-05-22-run11`
- `python -m pip install -e ./sdk` attempted first, but Windows blocked replacing the existing global `agentguard.exe` shim. The run continued with explicit `PYTHONPATH=./sdk` and verified repo-bound import.
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `agentguard demo`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`

## Proof artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `trace-inspection.txt`
- `trace-inspection.json`
- `demo-report.txt`
- `demo-incident.txt`
- `review-loop-report.txt`
- `review-loop-incident.txt`
- `focused-tests.txt`
- `release-guard.txt`
- `distribution-snapshot.txt`
- `github-release.json`
- `pypi-agentguard47.txt`
- `npm-mcp-version.json`
- `open-prs.json`
- `open-pr-review-threads.json`
- `open-issues.json`
- `pr-506-state-before-push.json`
- `pr-506-review-threads.json`

## Concrete guard behavior observed

The proof counted only raw trace events, not stdout-only success.

- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- Doctor trace emitted `doctor.verify=2`, proving local trace writing.

## Validation

- Focused SDK proof tests: `35 passed in 1.45s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Release/package snapshot: GitHub release, PyPI latest, and local SDK all align at `1.2.10`; npm and local MCP metadata align at `0.2.2`.
- Distribution snapshot: official MCP Registry still reports `0.2.1`; Glama API still returns an empty `tools` array.

## Repo health

- Staleness warning still applies: `ops/03-ROADMAP_NOW_NEXT_LATER.md` is `2 weeks ago`, and `ops/02-ARCHITECTURE.md` is `3 weeks ago`.
- Issue #473 remains the docs freshness tracker.
- PR #506 remains `REVIEW_REQUIRED` / `BLOCKED` pending human review.
- Open PR sweep found 23 open PRs before push.
- Highest-ROI next task remains distribution hygiene: refresh official MCP Registry metadata and get Glama to index the seven MCP tools.
