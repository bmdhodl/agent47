# Dogfood Operator Run 12 - 2026-05-23

## Goal

Keep a real AgentGuard-protected coding-agent workflow running against this repo and preserve durable proof that the SDK enforced runtime guardrails.

## Scope

- SDK-only proof artifacts under `proof/dogfood/2026-05-23/run12/`
- Rolling proof PR: `#506`
- Rolling proof issue: `#490`

## Non-goals

- No SDK behavior changes
- No dashboard, auth, billing, secrets, deployment, or paid-feature work
- No release cuts
- No duplicate proof PR

## Commands Run

PATH and repo-bound checks:

- `where.exe agentguard`
- `agentguard doctor`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

Validation:

- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

Repo health:

- `gh pr list --state open --limit 100 --json ...`
- `gh issue list --state open --limit 100 --json ...`
- `gh pr view 506 --json ...`
- GraphQL review-thread sweep across open PRs

## Import Binding

Repo-bound import resolved to:

`<repo>\sdk\agentguard\__init__.py`

PATH `agentguard.exe` resolved to `C:\Python313\Scripts\agentguard.exe` and `agentguard doctor` succeeded as a smoke check. The real proof path still used `PYTHONPATH=./sdk` to bind the active checkout.

## Guard Enforcement Observed

Demo trace: `agentguard_demo_traces.jsonl`

- `guard.budget_warning`: 1 event at `$0.84 / $1.00`
- `guard.budget_exceeded`: 1 event at `$1.0800 > $1.0000`
- `guard.loop_detected`: 1 event for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: 1 event for `fetch_docs` attempt 3 with limit 2

Coding-agent review-loop trace: `coding_agent_review_loop_traces.jsonl`

- `guard.budget_exceeded`: 1 event on review attempt 3 at `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: 1 event for `apply_patch` attempt 4 with limit 3

Doctor trace: `repo_agentguard_doctor_trace.jsonl`

- `doctor.verify`: start and end events emitted

Enforcement was real because the raw JSONL traces contain guard events with concrete budget, loop, and retry stop data, and the rendered incident reports classify the demo and review-loop runs as incidents.

## Validation Results

- Focused proof/CLI/metadata tests: `35 passed in 1.37s`
- Release guard: `Release guard passed.`

## Release And Distribution Snapshot

- GitHub latest release: `v1.2.10`
- PyPI `agentguard47`: `1.2.10`
- Local SDK version: `1.2.10`
- npm `@agentguard47/mcp-server`: `0.2.2`
- Local MCP package and server manifest: `0.2.2`
- MCP Registry direct server endpoint returned `404` from this run
- Glama listing still returns an empty `tools` array

## Repo Health Snapshot

- Open PRs: 25
- Active unresolved non-outdated review threads: 0
- PR `#506` is green but remains `REVIEW_REQUIRED` / `BLOCKED`
- PR `#508` is still failing CI from the `actions/setup-go` Dependabot bump guardrail expectation
- Issue `#473` still tracks stale roadmap/architecture docs
- Issues `#507` and `#469` remain SDK-only pip-audit reproduction items
- Issue `#490` remains the rolling dogfood proof sink

## Artifacts

- Raw demo trace: `proof/dogfood/2026-05-23/run12/agentguard_demo_traces.jsonl`
- Raw review-loop trace: `proof/dogfood/2026-05-23/run12/coding_agent_review_loop_traces.jsonl`
- Raw doctor trace: `proof/dogfood/2026-05-23/run12/repo_agentguard_doctor_trace.jsonl`
- Guard event extraction: `proof/dogfood/2026-05-23/run12/guard_events.json`
- Demo report: `proof/dogfood/2026-05-23/run12/demo-report.txt`
- Demo incident: `proof/dogfood/2026-05-23/run12/demo-incident.txt`
- Review-loop incident: `proof/dogfood/2026-05-23/run12/review-incident.txt`
- Repo health snapshot: `proof/dogfood/2026-05-23/run12/repo-health-snapshot.txt`
- Open PR review-thread sweep: `proof/dogfood/2026-05-23/run12/open-pr-review-thread-sweep.json`

## Recommended Next Task

Fix or recreate PR `#508` so the actionlint workflow guardrail expectation matches the Dependabot `actions/setup-go` v6.4.0 bump, then merge the green dependency PRs that are only waiting on human review.
