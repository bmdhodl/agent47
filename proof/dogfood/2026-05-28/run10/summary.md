# Dogfood run10 - 2026-05-28

## Goal
Keep a real AgentGuard workflow running against the public SDK repo and leave trace-backed proof plus a GitHub artifact.

## Scope
Touched only proof artifacts under `proof/dogfood/2026-05-28/run10/`. No SDK runtime, dashboard, auth, billing, deployment, or release code changed.

## Non-goals
No new guards, no paid features, no release cut, no dashboard work, and no broad cleanup.

## Done criteria
Matches `ops/04-DEFINITION_OF_DONE.md` for this proof-only PR: concrete runtime proof is saved, focused validation passes, no new dependencies are introduced, and docs/roadmap drift is reported instead of silently ignored.

## Commands run
- `where.exe agentguard`
- `python -c "import sys; print(sys.executable); import agentguard; print(agentguard.__file__); print(getattr(agentguard, '__version__', 'unknown'))"`
- `agentguard doctor --json --trace-file proof/dogfood/2026-05-28/run10/installed_doctor_trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-28/run10/installed_demo_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --json --trace-file proof/dogfood/2026-05-28/run10/repo_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run10/repo_demo_trace.jsonl`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-28/run10/repo_demo_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-28/run10/repo_demo_trace.jsonl --format markdown`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-28/run10/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-28/run10/coding_agent_review_loop_traces.jsonl --format markdown`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `python -m pip index versions agentguard47`
- `npm view @agentguard47/mcp-server version`

## Guard behavior observed
Trace inspection is saved in `trace_inspection.txt`; structured event inventory is saved in `guard_events.json`.

Repo-local demo emitted real guard events:
- `guard.budget_warning`
- `guard.budget_exceeded`: `Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})` 3 times
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Coding-agent review loop emitted real guard events:
- `guard.budget_exceeded` on review attempt 3
- `guard.retry_limit_exceeded` on patch attempt 4

Installed CLI smoke emitted the same demo guard events, but `python_agentguard_import.txt` shows the Python import path is bound to another checkout. The repo-local `PYTHONPATH=./sdk` commands are the canonical active-checkout proof.

## Validation
- Focused proof/distribution pytest: 35 passed in 1.58s.
- Release guard: passed with `--check-mcp-npm`.
- Artifact hygiene: UTF-8 without BOM, no NUL bytes, and local path markers redacted.
- GitHub release: `v1.2.10` published.
- PyPI: `agentguard47` latest and installed version are `1.2.10`.
- npm: `@agentguard47/mcp-server` is `0.2.2`.
- Official MCP Registry still reports package version `0.2.1`.
- Glama API still returns an empty `tools` array.

## Repo health notes
- Repo is public `bmdhodl/agent47`.
- Active proof sink is PR #540; it is mergeable and blocked by required human review.
- Roadmap freshness command reports 3 weeks old; architecture freshness command reports 4 weeks old. Existing issue #473 tracks this hygiene gap.
- PR #508 still has failed/cancelled CI on the setup-go dependency bump.
- Rolling dogfood issue remains #490.

## Artifact verdict
This run produced real AgentGuard enforcement proof. It is not status-only.
