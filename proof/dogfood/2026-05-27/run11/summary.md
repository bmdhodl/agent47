# AgentGuard Dogfood Proof - 2026-05-27 run11

Branch: `dogfood-2026-05-27-run9-worker`
Base commit before this run: `581c9dd`

## Goal

Keep the repo-local coding-agent workflow running under AgentGuard and refresh PR #529 with one more concrete proof bundle from the active checkout.

## Commands Run

- `agentguard doctor --trace-file global_agentguard_doctor_trace.jsonl`
- `agentguard demo --trace-file global_agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli report coding_agent_review_loop_traces.jsonl`
- `PYTHONNOUSERSITE=1 PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `<temp-venv>/Scripts/python.exe -m pip install -e ./sdk pytest`
- `<temp-venv>/Scripts/agentguard.exe doctor --trace-file installed_agentguard_doctor_trace.jsonl`
- `<temp-venv>/Scripts/agentguard.exe demo --trace-file installed_agentguard_demo_traces.jsonl`
- `<temp-venv>/Scripts/python.exe -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_guards.py::TestBudgetGuard sdk/tests/test_guards.py::TestLoopGuard sdk/tests/test_guards.py::TestRetryGuard -q`
- `git diff --check`

## Guard Behavior Observed

Real enforcement was observed in both checkout-bound and clean editable-install paths.

- `guard.budget_warning`: demo reached `$0.84` of a `$1.00` budget.
- `guard.budget_exceeded`: demo stopped at `$1.0800 > $1.0000`.
- `guard.loop_detected`: demo stopped repeated `tool.search({"query":"python asyncio"})` after 3 repeats.
- `guard.retry_limit_exceeded`: demo stopped `fetch_docs` after 3 attempts with a limit of 2.
- `guard.budget_exceeded`: review-loop proof stopped on attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: review-loop proof stopped repeated `apply_patch` on attempt 4 with a limit of 3.

## Trace Files

- `agentguard_doctor_trace.jsonl`: 4 events, setup trace only.
- `agentguard_demo_traces.jsonl`: 36 events, 4 guard events.
- `coding_agent_review_loop_traces.jsonl`: 14 events, 2 guard events.
- `installed_agentguard_doctor_trace.jsonl`: 4 events, setup trace only.
- `installed_agentguard_demo_traces.jsonl`: 36 events, 4 guard events.

## Validation

- Focused pytest: 31 passed.
- Guard-event parser found `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Artifact hygiene found no UTF-8 BOMs, NUL bytes, or local machine path leaks.
- `git diff --check` passed.

## Notes

The global `agentguard` entry point still fails before checkout code loads because the worker user-site points at stale editable package metadata. The active checkout and clean editable-install proof paths both passed.
