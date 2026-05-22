# Dogfood Proof - 2026-05-22 Run 6

## Goal

Keep the AgentGuard SDK running against its own repository with fresh local
proof that runtime guards enforce real stops, not just successful commands.

## Commands Run

- `python -m pip install -e ./sdk`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check`
- `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`
- `gh release view --json tagName,name,publishedAt,url`
- `python -m pip index versions agentguard47`
- `npm view @agentguard47/mcp-server version`
- `node -e "const p=require('./mcp-server/package.json'); const s=require('./mcp-server/server.json'); console.log(JSON.stringify({package:p.version,server:s.version,name:p.name}))"`
- `Invoke-RestMethod -Uri https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47`
- `Invoke-RestMethod -Uri https://registry.modelcontextprotocol.io/v0/servers/io.github.bmdhodl/agentguard47`

## Guard Behavior Observed

Raw traces show real local enforcement.

- `agentguard_demo_traces-run6.jsonl`
  - `guard.budget_warning`: emitted when demo spend reached `$0.84` of `$1.00`
  - `guard.budget_exceeded`: stopped demo spend at `$1.08 > $1.00`
  - `guard.loop_detected`: stopped repeated `tool.search({"query":"python asyncio"})`
  - `guard.retry_limit_exceeded`: stopped `fetch_docs` on attempt 3 with limit 2
- `coding_agent_review_loop_traces-run6.jsonl`
  - `guard.budget_exceeded`: stopped review loop on attempt 3 at `$0.0510 > $0.0450`
  - `guard.retry_limit_exceeded`: stopped `apply_patch` on attempt 4 with limit 3
- `agentguard_doctor_trace-run6.jsonl`
  - `doctor.verify`: emitted start and end events for local setup verification

## Artifacts

- `agentguard_doctor_trace-run6.jsonl`
- `agentguard_demo_traces-run6.jsonl`
- `coding_agent_review_loop_traces-run6.jsonl`
- `guard-events-run6.json`
- `demo-report-run6.md`
- `review-loop-incident-run6.md`
- `doctor-run6.out`
- `doctor-module-run6.out`
- `demo-run6.out`
- `review-loop-run6.out`

## Validation

- Focused pytest slice: 35 passed.
- MCP npm release guard: passed.
- `git diff --check`: clean.

## Repo Health

- Checkout verified as `https://github.com/bmdhodl/agent47.git` at `a2d9cce`.
- GitHub release and PyPI latest are aligned at `v1.2.10` / `agentguard47==1.2.10`.
- npm and local MCP metadata are aligned at `@agentguard47/mcp-server@0.2.2`.
- Glama listing is live, but the public API still returns an empty `tools` array.
- Direct MCP Registry server endpoint returned 404 from this environment.
- Ops freshness remains stale by repo policy as checked on 2026-05-22: roadmap last changed 13 days before this run, and architecture last changed 3 weeks before this run. Issue #473 tracks this.

## PR / Issue State

- Rolling dogfood issue: #490.
- Same-day dogfood PRs #495 through #499 are green but review-required.
- This run should update #490 and open a proof PR for the run6 artifact.

## Recommendation

Next highest-ROI task: refresh `ops/03-ROADMAP_NOW_NEXT_LATER.md` and
`ops/02-ARCHITECTURE.md`, then close or update issue #473 with the concrete
review outcome.
