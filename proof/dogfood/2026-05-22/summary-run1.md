# AgentGuard Dogfood Proof - 2026-05-22 run1

## Commands run

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`

The report and incident commands used the fresh root trace files produced by the run; those raw files were then copied into this proof directory with the `-run1` suffix.

## Repo binding

`PYTHONPATH` was set to this checkout's `sdk` directory. Import resolved to the repo-local `sdk/agentguard/__init__.py`.

## Guard behavior observed

Demo trace guard events:

- `guard.budget_exceeded`: 1
- `guard.budget_warning`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

Coding-agent review-loop trace guard events:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

The review-loop proof stopped on a real `BudgetGuard` event at `$0.0510 > $0.0450` during review attempt 3, then stopped an `apply_patch` retry storm through `RetryGuard` on attempt 4. The offline demo also exercised budget warning, hard budget stop, loop detection, and retry-limit enforcement.

## Enforcement verdict

Real enforcement observed. This run counts as dogfood proof because the raw JSONL traces contain guard events and the CLI report/incident output summarizes those events.

## Artifacts

- `proof/dogfood/2026-05-22/agentguard_doctor_trace-run1.jsonl`
- `proof/dogfood/2026-05-22/agentguard_demo_traces-run1.jsonl`
- `proof/dogfood/2026-05-22/coding_agent_review_loop_traces-run1.jsonl`
- `proof/dogfood/2026-05-22/agentguard_demo_report-run1.md`
- `proof/dogfood/2026-05-22/coding_agent_review_loop_incident-run1.md`
