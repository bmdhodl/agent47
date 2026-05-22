# AgentGuard Dogfood Proof - 2026-05-22 run7

## Scope

- Checkout: `bmdhodl/agent47`
- Branch: `codex/dogfood-proof-2026-05-22-run7`
- SDK binding: `PYTHONPATH=./sdk`; import resolved to `sdk/agentguard/__init__.py`
- Goal: prove repo-local AgentGuard enforcement in a real local coding-agent workflow.

## Commands Run

```text
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

## Guard Behavior Observed

The run counted only trace-backed guard behavior, not command success alone.

Demo trace:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

Coding-agent review-loop trace:

- `guard.budget_exceeded`: review attempt 3 stopped at `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 stopped after the retry limit of 3

## Artifacts

- `agentguard-demo-traces-run7.jsonl` - raw demo trace
- `coding-agent-review-loop-traces-run7.jsonl` - raw review-loop trace
- `agentguard_demo_traces.jsonl` - replay copy using the CLI output filename
- `coding_agent_review_loop_traces.jsonl` - replay copy using the example output filename
- `guard-events-run7.json` - parsed guard-event summary
- `agentguard-doctor-output.txt` - installed CLI doctor output
- `python-doctor-output.txt` - repo-local CLI doctor output
- `demo-output.txt` - demo command output
- `review-loop-output.txt` - coding-agent example output
- `demo-report.txt` - local report output
- `review-loop-incident.md` - local incident output

## Result

Enforcement was real. The raw trace files contain budget, loop, and retry guard events from deterministic offline workflows.
