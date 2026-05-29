# AgentGuard Dogfood Proof - 2026-05-29 run15

## Scope
- SDK-only recurring dogfood run.
- No dashboard, auth, billing, secrets, deployments, paid features, or release changes.
- Active checkout import resolved to `sdk/agentguard/__init__.py` with `agentguard47` version `1.2.10`.

## Commands Run
- `python -c "import agentguard..."` -> `exit_code=0`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run15/doctor_trace.jsonl --json` -> `exit_code=0`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-29/run15/demo_trace.jsonl` -> `exit_code=0`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py (from run15 proof dir)` -> `exit_code=0`
- `python -m agentguard.cli report proof/dogfood/2026-05-29/run15/demo_trace.jsonl` -> `exit_code=0`
- `python -m agentguard.cli report --json proof/dogfood/2026-05-29/run15/demo_trace.jsonl` -> `exit_code=0`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run15/demo_trace.jsonl` -> `exit_code=0`
- `python -m agentguard.cli incident --format markdown proof/dogfood/2026-05-29/run15/coding_agent_review_loop_traces.jsonl` -> `exit_code=0`
- `git log -1 --format='%cr' -- ops/03... and ops/02...` -> `exit_code=0`
- `gh release view --json tagName,name,publishedAt,url,isDraft,isPrerelease,targetCommitish` -> `exit_code=0`
- `python -m pip index versions agentguard47` -> `exit_code=0`
- `npm view @agentguard47/mcp-server version dist-tags.latest --json` -> `exit_code=0`
- `curl -sS -L https://registry.modelcontextprotocol.io/v0.1/servers?search=agentguard47` -> `exit_code=0`
- `Invoke-WebRequest https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47` -> `exit_code=0`

## Guard Behavior Observed
- `doctor_trace.jsonl`: `doctor.verify` start/end events were emitted.
- `demo_trace.jsonl`: `guard.budget_warning`, `guard.budget_exceeded` at `$1.0800 > $1.0000`, `guard.loop_detected` for repeated `tool.search`, and `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3 and `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.
- Enforcement was real: the demo/review-loop commands completed by catching guard exceptions and wrote trace events showing budget, loop, and retry stops.

## Release And Distribution Snapshot
- GitHub release: `v1.2.10` published `2026-05-02T15:48:03Z` at https://github.com/bmdhodl/agent47/releases/tag/v1.2.10.
- PyPI: `agentguard47` latest and installed are `1.2.10` according to `pip index`.
- npm MCP package: `0.2.2` with latest dist-tag `0.2.2`.
- Official MCP Registry: `io.github.bmdhodl/agentguard47` still reports server/package version `0.2.1` / `0.2.1`.
- Glama: API id `y6zuc6wgtu` still returns `tools` count `0` with environment schema present.

## Staleness
- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 3 weeks ago.
- `ops/02-ARCHITECTURE.md`: 4 weeks ago.
- This remains tracked by issue #473.

## Files
- Raw traces: `doctor_trace.jsonl`, `demo_trace.jsonl`, `coding_agent_review_loop_traces.jsonl`.
- Extracted guard events: `guard_events.json`.
- Command status map: `command_statuses.json`.
- Incident/report outputs: `demo_report*.out.txt`, `demo_incident.out.txt`, `review_loop_incident.out.txt`.
