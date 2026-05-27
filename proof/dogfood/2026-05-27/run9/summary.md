# AgentGuard Dogfood Run 9 - 2026-05-27

## Scope

SDK-only dogfood pass from commit `3f54935` in the public AgentGuard repo. No
dashboard, auth, billing, secrets, deployments, or release code was touched.

The checkout was in detached `HEAD` state. `ops/03-ROADMAP_NOW_NEXT_LATER.md`
is 3 weeks old and `ops/02-ARCHITECTURE.md` is 4 weeks old; issue #473 already
tracks this ops-cadence gap.

## Commands Run

Installed/global CLI path:

```powershell
agentguard doctor --trace-file agentguard_doctor_trace.jsonl
agentguard demo --trace-file agentguard_demo_traces.jsonl
```

Checkout-bound canonical path:

```powershell
$env:PYTHONPATH = "<repo>/sdk"
$env:PYTHONNOUSERSITE = "1"
python -m agentguard.cli doctor --trace-file agentguard_doctor_trace.jsonl
python -m agentguard.cli demo --trace-file agentguard_demo_traces.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli report coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

Validation:

```powershell
<temp-venv>/Scripts/python.exe -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_example_starters.py -q
git diff --check
```

## Guard Events Observed

`agentguard_demo_traces.jsonl` emitted these real guard events:

- `guard.budget_warning` at `$0.8400 / $1.0000`
- `guard.budget_exceeded` at `$1.0800 > $1.0000`
- `guard.loop_detected` for `tool.search({"query":"python asyncio"})` repeated 3 times
- `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2

`coding_agent_review_loop_traces.jsonl` emitted these real guard events:

- `guard.budget_exceeded` on review attempt 3 at `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3

Enforcement was real. The trace files contain emitted guard events and the
example output shows the BudgetGuard and RetryGuard stopped the simulated
coding-agent review loop.

## Installed CLI State

The global `agentguard` command is still not valid dogfood proof on this worker.
It fails before running because the user-site Python 3.13 environment has
corrupt/stale `agentguard47` metadata and raises:

```text
TypeError: 'NoneType' object is not subscriptable
```

The checkout-bound CLI path succeeds with `PYTHONPATH=<repo>/sdk` and
`PYTHONNOUSERSITE=1`.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `coding_agent_review_loop_incident.md`
- `guard_events.json`
- `trace_inspection.txt`
- command logs for installed CLI, checkout CLI, report, incident, venv setup,
  test dependency install, and focused pytest

## Validation Result

- Focused pytest: 21 passed in 1.06s
- `git diff --check`: passed
- Artifact hygiene: no UTF-8 BOMs and no NUL bytes in the run9 bundle
