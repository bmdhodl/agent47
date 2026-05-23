Dogfood operator run 9 proof published.

Artifacts:
- `proof/dogfood/2026-05-23/run9/summary_run9.md`
- `proof/dogfood/2026-05-23/run9/agentguard_demo_traces.jsonl`
- `proof/dogfood/2026-05-23/run9/coding_agent_review_loop_traces.jsonl`
- `proof/dogfood/2026-05-23/run9/demo_report.md`
- `proof/dogfood/2026-05-23/run9/demo_incident.md`
- `proof/dogfood/2026-05-23/run9/review_loop_incident.md`
- `proof/dogfood/2026-05-23/run9/guard_events_run9.json`
- `proof/dogfood/2026-05-23/run9/repo_health_run9.md`

Proof commands:
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

Concrete guard behavior:
- Demo emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo stopped budget at `$1.0800 > $1.0000`.
- Demo stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo stopped `fetch_docs` retry attempt 3 with limit 2.
- Review-loop proof emitted `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- Review-loop proof stopped `apply_patch` retry attempt 4 with limit 3.

Validation:
- Focused proof/metadata tests: `35 passed in 1.55s`.
- `python scripts\sdk_release_guard.py --check-mcp-npm`: `Release guard passed.`
- Artifact scan passed: UTF-8 without BOM, no NUL bytes, no local checkout path.

Repo health:
- PR `#506` is green but still `REVIEW_REQUIRED` / `BLOCKED`.
- All open PR review-thread sweep found 0 active unresolved non-outdated threads.
- PR `#508` has failing CI due the actionlint workflow guardrail test still expecting the old `actions/setup-go` v5 pin after Dependabot moved it to v6.4.0.
- Release/package state remains aligned for GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`; MCP Registry still reports `0.2.1`, and Glama still reports `tools=0`.
