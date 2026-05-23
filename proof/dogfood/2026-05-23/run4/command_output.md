# Dogfood command output

Repo-bound proof ran with `PYTHONPATH=./sdk` and resolved `agentguard` imports to `<repo>/sdk/agentguard/__init__.py`.

## Commands run

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-23/run4/agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-23/run4/coding_agent_review_loop_traces.jsonl`

## Concrete guard behavior observed

- Demo trace emitted `guard.budget_warning` at `$0.84 / $1.00`.
- Demo trace emitted `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- Demo trace emitted `guard.loop_detected` for repeated `tool.search`.
- Demo trace emitted `guard.retry_limit_exceeded` for `fetch_docs`.
- Review-loop trace emitted `guard.budget_exceeded` at `$0.0510 > $0.0450` on review attempt 3.
- Review-loop trace emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4.
