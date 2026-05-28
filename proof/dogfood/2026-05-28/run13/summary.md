# Dogfood Run 13 - 2026-05-28

## Scope

SDK-only recurring dogfood run for AgentGuard. This run refreshed PR #540
instead of opening another duplicate proof PR.

Non-goals: no dashboard, auth, billing, secrets, deployments, release cutting,
paid features, or new SDK features.

## Repo State

- Repo: `bmdhodl/agent47`
- Branch proof target: PR #540, `dogfood-2026-05-28-run8-worker`
- Local proof commit base: `951c9870ce23cf07a4934433d5561fcff5845932`
- SDK version: `1.2.10`
- GitHub release: `v1.2.10`
- PyPI latest: `agentguard47==1.2.10`
- npm MCP latest: `@agentguard47/mcp-server@0.2.2`
- Glama API: listing live, `tools: []`
- Direct MCP Registry server endpoint: returned 404 from this environment

Staleness warning remains active:

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 3 weeks ago
- `ops/02-ARCHITECTURE.md`: 4 weeks ago
- Existing tracker: issue #473

## Commands Run

Installed CLI smoke:

```powershell
agentguard doctor --trace-file proof/dogfood/2026-05-28/run13/installed_doctor_trace.jsonl --json
agentguard demo --trace-file proof/dogfood/2026-05-28/run13/installed_demo_trace.jsonl
```

Canonical repo-local proof:

```powershell
$env:PYTHONPATH='./sdk'
python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run13/repo_doctor_trace.jsonl --json
python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run13/repo_demo_trace.jsonl
python -m agentguard.cli report proof/dogfood/2026-05-28/run13/repo_demo_trace.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-28/run13/repo_demo_trace.jsonl --format markdown
python examples/coding_agent_review_loop.py
python -m agentguard.cli report proof/dogfood/2026-05-28/run13/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-28/run13/coding_agent_review_loop_traces.jsonl --format markdown
```

Validation:

```powershell
python -m pytest sdk/tests/test_doctor.py sdk/tests/test_demo.py sdk/tests/test_quickstart.py sdk/tests/test_pypi_readme_sync.py sdk/tests/test_dashboard_handoff_docs.py sdk/tests/test_sdk_release_guard.py -q
python scripts/sdk_release_guard.py --check-mcp-npm
git diff --check
```

## Guard Behavior Observed

Enforcement was real. The raw JSONL traces contain guard events from the active
repo-local SDK path.

`repo_demo_trace.jsonl`:

- `guard.budget_warning`: cost used `0.84`, limit `1.0`
- `guard.budget_exceeded`: `Cost budget exceeded: $1.0800 > $1.0000`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

`coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: attempt 3, cost `$0.0510 > $0.0450`, 12,300 tokens used
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 with limit 3

`repo_doctor_trace.jsonl`:

- `doctor.verify=2`
- `reasoning.step=1`
- `tool.check=1`

Installed CLI comparison proof emitted the same demo guard events, but the
installed `agentguard` import path still resolves to another local checkout.
The canonical proof for this PR is therefore the repo-local `PYTHONPATH=./sdk`
run.

## Artifacts

- `repo_doctor_trace.jsonl`
- `repo_doctor_output.json`
- `repo_demo_trace.jsonl`
- `repo_demo_output.txt`
- `repo_demo_report.txt`
- `repo_demo_incident.md`
- `coding_agent_review_loop_traces.jsonl`
- `review_loop_output.txt`
- `review_loop_report.txt`
- `review_loop_incident.md`
- `installed_doctor_trace.jsonl`
- `installed_doctor_output.json`
- `installed_demo_trace.jsonl`
- `installed_demo_output.txt`
- `trace_inspection.txt`
- `guard_events.json`
- `focused_pytest_output.txt`
- `release_guard_output.txt`
- `diff_check_output.txt`
- `pr_540_snapshot.json`
- `open_prs_snapshot.json`
- `open_issues_snapshot.json`
- `issue_490_snapshot.json`
- `issue_473_snapshot.json`

## Validation Result

- Focused pytest: `43 passed in 1.37s`
- Release guard: passed
- `git diff --check`: passed
- Artifact hygiene: UTF-8, no BOM/NUL/local-path leaks, JSON/JSONL parse clean

## Repo Health

- PR #540 is the active dogfood proof PR and is blocked only by required human review.
- PR #541 is green and review-blocked after correcting an overstated README claim.
- The growing dogfood proof PR queue remains green/review-blocked.
- Issue #490 remains the rolling dogfood proof log.
- Issue #473 remains the ops freshness tracker.

## Recommended Next Task

Get human review/merge for the green dogfood proof queue, starting with #540.
After that, run a narrow ops-doc freshness pass for #473.
