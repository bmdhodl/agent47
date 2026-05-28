# AgentGuard Dogfood Proof - 2026-05-28 Run 9

Runtime: 2026-05-28T05:58:08.1084976-05:00

## Commands run

```powershell
gh auth status
git fetch origin --prune
git rev-parse --show-toplevel
git rev-parse HEAD
git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md
git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md
gh pr list --state open --json number,title,headRefName,mergeStateStatus,reviewDecision,statusCheckRollup,updatedAt,url
gh pr view 540 --json number,title,headRefName,mergeStateStatus,reviewDecision,statusCheckRollup,comments,reviews,url
gh api graphql ... reviewThreads for PR 540
gh issue list --state open --limit 30 --json number,title,labels,updatedAt,url
gh release view --json tagName,publishedAt,url,name
python -c "fetch PyPI and npm package metadata"
python -c "fetch Glama and official MCP Registry metadata"
agentguard doctor --trace-file proof/dogfood/2026-05-28/run9/installed_doctor_trace.jsonl
python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run9/doctor_trace.jsonl --json
python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run9/demo_trace.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report proof/dogfood/2026-05-28/run9/demo_trace.jsonl
python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run9/demo_trace.jsonl
python -m agentguard.cli report proof/dogfood/2026-05-28/run9/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-28/run9/coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts/sdk_release_guard.py --check-mcp-npm
git diff --check
```

## Guard behavior observed

Enforcement was real. The demo trace emitted:

- `guard.budget_warning` with `cost_used: 0.84`, `limit_usd: 1.0`
- `guard.budget_exceeded` with `cost_used: 1.08`, `limit_usd: 1.0`
- `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded` for `fetch_docs` retry attempt 3 with limit 2

The coding-agent review-loop trace emitted:

- `guard.budget_exceeded` on review attempt 3 with `cost_usd: 0.051` over `0.045`
- `guard.retry_limit_exceeded` on `apply_patch` attempt 4 with limit 3

## Artifact files

- `installed_doctor_trace.jsonl` - installed CLI doctor trace
- `installed_doctor_output.txt` - installed CLI doctor transcript
- `doctor_trace.jsonl` - repo-local doctor trace
- `doctor_output.json` - repo-local doctor JSON output
- `demo_trace.jsonl` - raw demo trace
- `demo_output.txt` - demo transcript
- `demo_report.txt` - demo report output
- `demo_incident.md` - demo incident report
- `coding_agent_review_loop_traces.jsonl` - raw review-loop trace
- `review_loop_output.txt` - review-loop transcript
- `review_loop_report.txt` - review-loop report output
- `review_loop_incident.md` - review-loop incident report
- `trace_inspection.txt` - extracted guard-event inspection
- `pr_540_state.json` - PR review/check snapshot
- `rolling_issue_490_state.json` - rolling issue snapshot

## Repo and distribution checks

- Repo identity: `bmdhodl/agent47`
- Base commit before dogfood branch artifact: `b0e872025e0b0980555ad5b3d376ec28f481744b`
- SDK package metadata: `agentguard47` version `1.2.10`
- Latest GitHub release: `v1.2.10`, published 2026-05-02
- PyPI latest: `agentguard47` version `1.2.10`
- npm latest: `@agentguard47/mcp-server` version `0.2.2`
- Official MCP Registry still reports `io.github.bmdhodl/agentguard47` package version `0.2.1`
- Glama API returned HTTP 403 from this environment, so tool indexing was not revalidated live

## Staleness check

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 3 weeks ago, stale by the repo's 5-day threshold
- `ops/02-ARCHITECTURE.md`: 4 weeks ago, stale by the repo's 14-day threshold
- Existing tracker: issue #473

## PR and issue snapshot

- PR #540 is green on visible checks but remains `REVIEW_REQUIRED` / `BLOCKED`.
- PR #540 review-thread sweep returned zero review threads.
- Open security/dependency issues #469 and #507 remain real follow-ups, but the current dogfood proof did not expose a new SDK runtime blocker.
- Follow-up file still points to Glama tool indexing and MCP Registry metadata refresh as distribution tasks.

## Validation

- Focused proof/distribution tests: 35 passed in 1.47s.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: clean.
- Artifact hygiene: UTF-8, no BOM/NUL, and no local absolute path leakage after normalization.

## Result

Dogfood proof succeeded. AgentGuard enforced budget, loop, and retry behavior in the offline demo, and budget plus retry behavior in the repo-local coding-agent review-loop proof.
