# Dogfood operator run 16 - 2026-05-22

## Goal

Keep a real coding-agent workflow running under AgentGuard and leave durable proof that local guard enforcement still works.

## Scope

- Proof artifacts under `proof/dogfood/2026-05-22/run16/`
- No SDK runtime, dashboard, auth, billing, deployment, release, or paid-feature changes

## Commands run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_example_starters.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

Raw trace inspection confirmed real enforcement:

- `agentguard_demo_traces.jsonl`: `guard.budget_warning=1`, `guard.budget_exceeded=1`, `guard.loop_detected=1`, `guard.retry_limit_exceeded=1`
- `coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded=1`, `guard.retry_limit_exceeded=1`

Concrete stops:

- Demo budget enforcement stopped at `$1.0800 > $1.0000`
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with limit 2
- Review-loop budget enforcement stopped attempt 3 at `$0.0510 > $0.0450`
- Review-loop retry enforcement stopped `apply_patch` attempt 4

## Validation

- Focused SDK proof tests: `35 passed in 1.60s`
- Release guard with npm check: `Release guard passed.`

## Notes

- The run used repo-bound imports via `PYTHONPATH=./sdk`; the public import-binding artifact redacts the local checkout path.
- This proof-only branch still shows the known review-loop incident estimated-cost drift: incident output reports `$0.1020` while the raw guard event proves `$0.0510 > $0.0450` enforcement. PR #502 already carries the code fix and remains review-blocked.
- Repo freshness warning still applies: roadmap is 2 weeks old and architecture is 3 weeks old; issue #473 tracks the refresh.
