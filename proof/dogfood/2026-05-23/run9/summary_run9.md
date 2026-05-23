# AgentGuard Dogfood Proof - 2026-05-23 Run 9

## Goal

Keep one real coding-agent workflow running under AgentGuard from the active SDK checkout, then preserve the proof in the repo and on GitHub.

## Checkout

- Repo: `bmdhodl/agent47`
- Proof branch: `codex/dogfood-proof-2026-05-22-run11`
- Run folder: `proof/dogfood/2026-05-23/run9/`
- Repo-bound import: `<checkout>\sdk\agentguard\__init__.py`

## Commands Run

```powershell
where.exe agentguard
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts\sdk_release_guard.py --check-mcp-npm
```

## Guard Behavior Observed

This was real guard enforcement, not stdout-only success.

- `agentguard demo` emitted `guard.budget_warning` at `$0.84 / $1.00`.
- `agentguard demo` emitted `guard.budget_exceeded`: `$1.0800 > $1.0000`.
- `agentguard demo` emitted `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- `agentguard demo` emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- `examples/coding_agent_review_loop.py` emitted `guard.budget_exceeded` on review attempt 3: `$0.0510 > $0.0450`.
- `examples/coding_agent_review_loop.py` emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

## Artifact Files

- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard_doctor_path_output.txt`
- `doctor_output.txt`
- `demo_output.txt`
- `review_loop_output.txt`
- `demo_report.md`
- `demo_incident.md`
- `review_loop_incident.md`
- `guard_events_run9.json`
- `trace_inspection_output.txt`
- `focused_tests_output.txt`
- `release_guard_output.txt`
- `where_agentguard.txt`
- `import_binding.txt`

## Validation

- Focused proof and metadata tests: `35 passed in 1.55s`
- Release guard: `Release guard passed.`

## Result

Dogfood proof passed. AgentGuard stopped a budget overrun, a repeated-tool loop, and a retry storm in fresh local traces from the active checkout.
