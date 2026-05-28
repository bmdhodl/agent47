# AgentGuard Dogfood Proof - 2026-05-28 Run 8

Runtime: 2026-05-28T04:55:45.7910301-05:00

## Commands run

```powershell
gh auth status
git fetch origin --prune
git rev-parse HEAD
git rev-parse origin/main
git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md
git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md
gh pr list --state open --limit 50 --json number,title,headRefName,mergeStateStatus,reviewDecision,updatedAt
gh issue list --state open --limit 30 --json number,title,labels,updatedAt,assignees
gh release view --json tagName,name,publishedAt,isDraft,isPrerelease,url,targetCommitish
python -c "import urllib.request,json; ..."
agentguard doctor --trace-file proof/dogfood/2026-05-28/run8/doctor_trace.jsonl --json
agentguard demo --trace-file proof/dogfood/2026-05-28/run8/demo_trace.jsonl
python examples/coding_agent_review_loop.py
agentguard report proof/dogfood/2026-05-28/run8/demo_trace.jsonl
agentguard incident --format markdown proof/dogfood/2026-05-28/run8/demo_trace.jsonl
agentguard report proof/dogfood/2026-05-28/run8/coding_agent_review_loop_traces.jsonl
agentguard incident --format markdown proof/dogfood/2026-05-28/run8/coding_agent_review_loop_traces.jsonl
```

## Guard behavior observed

Enforcement was real. The demo trace emitted:

- `guard.budget_exceeded` with `cost_used: 1.08`, `limit_usd: 1.0`
- `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded` for `fetch_docs` retry attempt 3 with limit 2

The coding-agent review-loop trace emitted:

- `guard.budget_exceeded` on review attempt 3 with `cost_usd: 0.051` over `0.045`
- `guard.retry_limit_exceeded` on `apply_patch` attempt 4 with limit 3

## Artifact files

- `doctor_trace.jsonl` - raw doctor trace
- `doctor_output.json` - doctor command output
- `demo_trace.jsonl` - raw demo trace
- `demo_output.txt` - demo transcript
- `demo_report.txt` - demo report output
- `demo_incident.md` - demo incident report
- `coding_agent_review_loop_traces.jsonl` - raw review-loop trace
- `review_loop_output.txt` - review-loop transcript
- `review_loop_report.txt` - review-loop report output
- `review_loop_incident.md` - review-loop incident report

## Repo and distribution checks

- Repo identity: `bmdhodl/agent47`
- `HEAD` and `origin/main`: `b0e872025e0b0980555ad5b3d376ec28f481744b`
- SDK package metadata: `agentguard47` version `1.2.10`
- Latest GitHub release: `v1.2.10`, published 2026-05-02
- PyPI latest: `agentguard47` version `1.2.10`
- npm latest: `@agentguard47/mcp-server` version `0.2.2`

## Staleness check

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 3 weeks ago, stale by the repo's 5-day threshold
- `ops/02-ARCHITECTURE.md`: 4 weeks ago, stale by the repo's 14-day threshold
- Existing tracker: issue #473

## Open queue snapshot

- Latest dogfood PRs #532 through #539 were green or already reported green in the live PR list, but blocked by required human review.
- PR #508 remains a higher-ROI dependency/CI follow-up than adding another feature.
- Issues #469 and #507 track security/dependency audit findings and should stay visible.
- Follow-up file still points to Glama tool indexing and MCP Registry metadata refresh as distribution tasks.

## Result

Dogfood proof succeeded. AgentGuard enforced budget, loop, and retry behavior in the offline demo, and budget plus retry behavior in the repo-local coding-agent review-loop proof.
