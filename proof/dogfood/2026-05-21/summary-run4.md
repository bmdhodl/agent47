# AgentGuard Dogfood Proof - 2026-05-21 run 4

## Scope

- Repo: `bmdhodl/agent47`
- Checkout: public SDK repo worktree
- SDK binding: repo-local `sdk/agentguard/__init__.py`
- Dogfood proof commands: no API keys and no external service configuration
- Release/package validation: `sdk_release_guard.py --check-mcp-npm` performs an npm registry check and uses network without secrets
- Purpose: verify AgentGuard emits real local guard enforcement events during a recurring coding-agent style workflow

## Commands run

```powershell
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts\sdk_release_guard.py --check-mcp-npm
```

The CLI and example commands generated unsuffixed trace files in the repo root. For archival clarity in this dated proof folder, those files were copied to the `*-run4.*` names listed below.

## Guard behavior observed

`agentguard_demo_traces-run4.jsonl`:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1
- Maximum per-event `cost_usd`: `$0.1200`

`coding_agent_review_loop_traces-run4.jsonl`:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1
- Review-loop budget stop: `$0.0510 > $0.0450`
- Retry stop: `apply_patch` attempt 4 with limit 3
- Maximum per-event `cost_usd`: `$0.0205`

`agentguard_doctor_trace-run4.jsonl`:

- `doctor.verify`: 2

## Artifacts

- `import-binding-run4.txt`
- `agentguard-doctor-path-run4.txt`
- `agentguard-doctor-module-run4.txt`
- `agentguard-demo-output-run4.txt`
- `agentguard-demo-report-run4.txt`
- `agentguard_demo_traces-run4.jsonl`
- `agentguard_doctor_trace-run4.jsonl`
- `coding-agent-review-loop-output-run4.txt`
- `coding-agent-incident-run4.md`
- `coding_agent_review_loop_traces-run4.jsonl`

## Validation

- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q` -> `35 passed in 1.57s`
- `python scripts\sdk_release_guard.py --check-mcp-npm` -> `Release guard passed.`

## Result

Enforcement was real for this repo-local proof run. The raw trace files contain concrete guard events for budget warning, budget exceeded, loop detection, and retry-limit enforcement. No SDK code changes were needed.
