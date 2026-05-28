# AgentGuard dogfood run 7 - 2026-05-28

## Scope

- Repo: `bmdhodl/agent47`
- Branch: `dogfood-2026-05-28-run7-worker`
- SDK-only dogfood proof. No dashboard, auth, billing, secrets, deployments, paid features, or release work.
- Canonical proof path used the repo-local SDK with `PYTHONPATH=./sdk` because the PATH `agentguard` shim resolves to another checkout.

## Commands run

```powershell
git status --short --branch
git remote -v
git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md
git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md
gh auth status
gh pr list --state open --limit 20 --json number,title,headRefName,baseRefName,isDraft,mergeable,reviewDecision,statusCheckRollup,updatedAt,url
gh issue list --state open --limit 30 --json number,title,labels,updatedAt,url
gh release view --json tagName,publishedAt,url,isPrerelease,isDraft,name
python -m pip index versions agentguard47
npm view @agentguard47/mcp-server version
$env:PYTHONPATH=(Resolve-Path .\sdk).Path
python -c "import agentguard, sys; print(agentguard.__file__); print(sys.executable)"
python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl
python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts/sdk_release_guard.py --check-mcp-npm
```

## Guard behavior observed

Trace inspection is saved in `trace_inspection.txt` and parsed guard events are saved in `guard_events.json`.

- `agentguard_doctor_trace.jsonl`: 4 local setup events, no guard enforcement expected.
- `agentguard_demo_traces.jsonl`: 36 events and 4 guard events.
  - `guard.budget_warning`: warning fired at 84% of the $1.00 demo budget.
  - `guard.budget_exceeded`: stopped at $1.0800 > $1.0000.
  - `guard.loop_detected`: stopped repeated `tool.search({"query":"python asyncio"})` after 3 repeats.
  - `guard.retry_limit_exceeded`: stopped `fetch_docs` on attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl`: 14 events and 2 guard events.
  - `guard.budget_exceeded`: stopped the review loop at $0.0510 > $0.0450.
  - `guard.retry_limit_exceeded`: stopped `apply_patch` on attempt 4 with limit 3.

## Enforcement verdict

Real enforcement observed. The proof does not rely on exit codes alone: the raw JSONL traces, parsed `guard_events.json`, CLI report, and incident report all show guard behavior.

## Validation

- Focused proof tests: 35 passed in 1.45s.
- Release guard with MCP npm check: passed.
- Release/distribution state: GitHub release `v1.2.10`, PyPI `agentguard47==1.2.10`, npm `@agentguard47/mcp-server==0.2.2`.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `doctor_stdout.txt`
- `demo_stdout.txt`
- `review_loop_stdout.txt`
- `demo_report.txt`
- `review_loop_incident.md`
- `trace_inspection.txt`
- `guard_events.json`
- `summary.md`
