# AgentGuard Dogfood Proof - 2026-05-22 Run 9

## Scope

- Repo: `bmdhodl/agent47`
- Branch: `codex/dogfood-proof-2026-05-22-run9`
- SDK scope only. No dashboard, auth, billing, deployment, paid feature, or release work.
- Repo-bound import proof resolved to `<repo_root>/sdk/agentguard/__init__.py`.

## Commands Run

```powershell
git rev-parse --show-toplevel
git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md
git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md
gh pr list --limit 20 --json number,title,headRefName,reviewDecision,mergeStateStatus,statusCheckRollup,url
gh issue list --limit 30 --json number,title,labels,state,updatedAt,url
gh release view --json tagName,publishedAt,url,name
npm view @agentguard47/mcp-server version
python -m pip index versions agentguard47
$env:PYTHONPATH=(Resolve-Path .\sdk).Path
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

The runtime commands generated the root-level trace files with their default
names. Those files were then copied into this proof folder with `_run9`
suffixes so repeated runs on the same date do not overwrite prior artifacts.

## Guard Events Observed

### `agentguard_demo_traces_run9.jsonl`

- `guard.budget_warning`: cost reached `$0.84` of `$1.00`.
- `guard.budget_exceeded`: cost reached `$1.0800 > $1.0000`; this call added `$0.1200`.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2.

### `coding_agent_review_loop_traces_run9.jsonl`

- `guard.budget_exceeded`: review attempt 3 reached `$0.0510 > $0.0450` after 12,300 tokens; this call added `$0.0205`.
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 exceeded retry limit 3.

## Enforcement Verdict

Real enforcement confirmed. This run is not counted from command success alone:

- BudgetGuard stopped both the offline demo and coding-agent review loop after explicit cost thresholds were crossed.
- LoopGuard stopped repeated `tool.search` calls in the offline demo.
- RetryGuard stopped both `fetch_docs` retry churn and `apply_patch` retry churn.
- Incident output reported critical guard events and estimated savings for the stopped review-loop overrun.

## Freshness And Repo Health

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: `2 weeks ago`; AGENTS.md requires a
  warning when the roadmap freshness check is older than 5 days.
- `ops/02-ARCHITECTURE.md`: `3 weeks ago`; AGENTS.md requires a warning when
  the architecture freshness check is older than 14 days.
- Latest GitHub release: `v1.2.10`, published 2026-05-02.
- PyPI latest: `agentguard47==1.2.10`.
- npm latest: `@agentguard47/mcp-server@0.2.2`.
- Local SDK version: `1.2.10`.
- Local MCP metadata: `0.2.2`.

## Artifacts

- `proof/dogfood/2026-05-22/agentguard_doctor_trace_run9.jsonl`
- `proof/dogfood/2026-05-22/agentguard_demo_traces_run9.jsonl`
- `proof/dogfood/2026-05-22/coding_agent_review_loop_traces_run9.jsonl`
- `proof/dogfood/2026-05-22/agentguard_demo_report_run9.txt`
- `proof/dogfood/2026-05-22/coding_agent_review_loop_incident_run9.md`

All run 9 proof files were checked as valid UTF-8 with zero NUL bytes.
