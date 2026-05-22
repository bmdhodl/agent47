# AgentGuard Dogfood Proof - 2026-05-22 Run 2

## Scope

SDK-only dogfood run from `C:\Users\patri\.codex\worktrees\3b98\agent47`.

The run used the repo-local SDK through:

```powershell
$env:PYTHONPATH = "C:\Users\patri\.codex\worktrees\3b98\agent47\sdk"
```

Import proof resolved to:

```text
C:\Users\patri\.codex\worktrees\3b98\agent47\sdk\agentguard\__init__.py
```

## Commands Run

```powershell
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts\sdk_release_guard.py --check-mcp-npm
git diff --check
```

## Guard Events Observed

`agentguard_demo_traces-run2.jsonl`:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

`coding_agent_review_loop_traces-run2.jsonl`:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Concrete review-loop enforcement:

- BudgetGuard stopped review attempt 3 at `$0.0510 > $0.0450`.
- RetryGuard stopped `apply_patch` attempt 4 with limit 3.

## Enforcement Verdict

Real enforcement was observed. This run does not count command success alone as proof; it relies on raw JSONL guard events from the demo and coding-agent review-loop traces.

## Artifacts

- `agentguard_demo_traces-run2.jsonl`
- `coding_agent_review_loop_traces-run2.jsonl`
- `agentguard_doctor_trace-run2.jsonl`
- `doctor-path-command-run2.txt`
- `doctor-module-command-run2.txt`
- `demo-command-run2.txt`
- `coding-agent-review-loop-command-run2.txt`
- `demo-report-run2.md`
- `coding-agent-incident-run2.md`
- `guard-events-run2.json`
