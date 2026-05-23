# Dogfood operator run 8 - 2026-05-23

## Goal

Keep a real AgentGuard-protected agent workflow running against the public SDK checkout and leave durable proof in the rolling dogfood PR.

## Scope

- SDK-only dogfood proof artifacts under `proof/dogfood/2026-05-23/run8/`.
- Rolling GitHub proof flow on PR #506 and issue #490.

## Non-goals

- No SDK runtime changes.
- No dashboard, auth, billing, secrets, deployments, or paid-feature work.
- No release cut.

## Done criteria

Per `ops/04-DEFINITION_OF_DONE.md`, this run is done when the proof path is trace-backed, focused validation passes, no hard dependencies are added, and the PR carries concrete evidence.

## Commands run

- `git fetch origin codex/dogfood-proof-2026-05-22-run11`
- `git switch codex/dogfood-proof-2026-05-22-run11`
- `python -m pip install -e ./sdk`
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
- `artifact-scan.txt`
- `open-prs.json`
- `open-issues.json`
- `pr-506-state-before-push.json`
- `pr-506-review-threads.json`
- `pr-506-review-comments.json`
- `open-pr-review-threads.json`
- release, package, MCP Registry, and Glama snapshots

## Concrete guard behavior observed

The proof counted raw trace events, not stdout-only success.

- Demo trace emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with limit 2.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- Doctor trace emitted `doctor.verify=2`, proving local trace writing.

## Validation

- Repo binding: `import-binding.txt` resolved `agentguard` to `<repo>\sdk\agentguard\__init__.py`.
- `agentguard doctor`, `python -m agentguard.cli doctor`, `agentguard demo`, `python -m agentguard.cli demo`, and the review-loop example all ran successfully.
- Focused SDK proof tests: `35 passed in 1.95s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Artifact local-path/BOM/NUL/JSON scan: passed.
- `python -m pip install -e ./sdk` failed because Windows denied access to an existing `agentguard.exe`; proof still used the checkout via `PYTHONPATH=./sdk`.

## Repo health

- Staleness warning still applies: `ops/03-ROADMAP_NOW_NEXT_LATER.md` is `2 weeks ago`, and `ops/02-ARCHITECTURE.md` is `3 weeks ago`.
- Issue #473 remains the docs freshness tracker.
- New issue #507 reports pip-audit findings against dev/package tooling and needs SDK-only reproduction before treating it as a runtime blocker.
- PR #508 is failing CI after the `actions/setup-go` Dependabot bump; likely next action is inspect the failed test logs or ask Dependabot to rebase/recreate.
- PR #506 remains the consolidated proof PR and was `REVIEW_REQUIRED` / `BLOCKED` before this run's push.
- Release/package snapshot: GitHub release, PyPI latest, and local SDK align at `1.2.10`; npm and local MCP metadata align at `0.2.2`.
- Distribution snapshot: official MCP Registry still reports `0.2.1`; Glama API still returns an empty `tools` array.

## Docs updates needed

No docs update is needed for this artifact-only run. Existing docs freshness remains tracked by #473.
