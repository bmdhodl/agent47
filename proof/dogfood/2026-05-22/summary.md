# AgentGuard Dogfood Proof - 2026-05-22

## Scope

- Repo: `bmdhodl/agent47`
- SDK import binding: `sdk/agentguard/__init__.py`
- Core dogfood commands used no API keys, no dashboard, and no network calls.
- Networked repo-health checks were run separately for GitHub, PyPI, npm, and release metadata.

## Commands Run

```bash
git rev-parse --show-toplevel
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts/sdk_release_guard.py --check-mcp-npm
```

## Guard Behavior Observed

`agentguard_demo_traces.jsonl`:

- `guard.budget_warning`: warning at `$0.84` of `$1.00`.
- `guard.budget_exceeded`: stopped at `$1.0800 > $1.0000`.
- `guard.loop_detected`: stopped repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: stopped `fetch_docs` on attempt 3 with limit 2.

`coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: stopped review attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: stopped `apply_patch` retry storm on attempt 4 with limit 3.

Enforcement was real. The proof includes raw traces, rendered report output, rendered incident output, and focused regression output.

## Fix Made During This Run

Prior dogfood review comments exposed that `examples/coding_agent_review_loop.py` emitted cumulative budget spend as `data.cost_usd` on `guard.budget_exceeded`. Reporters treat `cost_usd` fields as additive, so the incident report showed `$0.1020` instead of the real `$0.0510` review-loop total.

This run changed that guard-event field to `cost_used`, added regression coverage, and refreshed the checked-in sample incident report. The regenerated incident artifact now reports `Estimated cost: $0.0510`.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard_demo_report.txt`
- `agentguard_demo_incident.md`
- `coding_agent_review_loop_incident.md`
- `trace_event_inspection.txt`
- `focused_tests.txt`
