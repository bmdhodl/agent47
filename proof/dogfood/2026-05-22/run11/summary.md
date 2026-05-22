# AgentGuard Dogfood Proof - 2026-05-22 Run 11

## Repo Identity

- Repo: `https://github.com/bmdhodl/agent47.git`
- Checkout: `<worktree>\agent47`
- Branch: `codex/dogfood-proof-2026-05-22-run11`
- SDK import proof: `<worktree>\agent47\sdk\agentguard\__init__.py`
- PATH CLI: `<python-scripts>\agentguard.exe`

## Commands Run

- `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

## Guard Behavior Observed

AgentGuard enforcement was real. This run does not rely on command success alone.

`agentguard_demo_traces.jsonl` emitted:

- `guard.budget_warning`: cost reached `$0.84` of a `$1.00` limit.
- `guard.budget_exceeded`: cost reached `$1.0800 > $1.0000`.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2.

`coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded`: review attempt 3 stopped at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: `apply_patch` attempted 4 times with limit 3.

## Proof Files

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo_report.txt`
- `review_loop_report.txt`
- `demo_incident.md`
- `review_loop_incident.md`

## Health Notes

- `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 2 weeks old.
- `ops/02-ARCHITECTURE.md` is 3 weeks old.
- Issue `#473` remains the active stale-docs tracker.
- The review-loop trace enforces the budget at `$0.0510`, but `agentguard report` and `agentguard incident` currently estimate `$0.1020` for that same proof file. This appears to be the known cost-accounting drift already tracked by PR `#502`.
- Open PRs remain blocked on review approval rather than CI.

## Release And Distribution Snapshot

- GitHub latest release: `v1.2.10`
- Local SDK package version: `1.2.10`
- npm `@agentguard47/mcp-server`: `0.2.2`
- Local MCP metadata: `0.2.2`
- Known distribution drift remains: official MCP Registry metadata can still lag at `0.2.1`, and Glama indexing has recently returned `tools: []`.
