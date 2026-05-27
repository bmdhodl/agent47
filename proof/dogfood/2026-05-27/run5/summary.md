# AgentGuard dogfood run 5 - 2026-05-27

## Scope

- Checkout: `3f54935b2484bc88a8c5438d032dbfb37f5e94c4`
- SDK-only dogfood proof for local AgentGuard enforcement.
- No dashboard, secrets, billing, deployment, paid-feature, or release work.

## Commands run

Installed entry point, captured as environment health evidence:

```powershell
agentguard doctor --trace-file proof/dogfood/2026-05-27/run5/installed_doctor_trace.jsonl
agentguard demo --trace-file proof/dogfood/2026-05-27/run5/installed_demo_trace.jsonl
```

Active checkout proof, isolated from the broken user-site editable install:

```powershell
$env:PYTHONPATH = "sdk"
$env:PYTHONNOUSERSITE = "1"
python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run5/checkout_doctor_trace.jsonl
python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run5/checkout_demo_trace.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report proof/dogfood/2026-05-27/run5/checkout_demo_trace.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-27/run5/checkout_demo_trace.jsonl
python -m agentguard.cli report proof/dogfood/2026-05-27/run5/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-27/run5/coding_agent_review_loop_traces.jsonl
```

## Guard behavior observed

The active checkout proof showed real enforcement, not just successful command exits.

- `guard.budget_warning`: demo warned at `$0.84` against a `$1.00` limit.
- `guard.budget_exceeded`: demo stopped on call 9 at `$1.08 > $1.00`.
- `guard.loop_detected`: demo stopped repeated `tool.search` calls after 3 repeats.
- `guard.retry_limit_exceeded`: demo stopped `fetch_docs` on retry 3 with limit 2.
- `guard.budget_exceeded`: review-loop proof stopped attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: review-loop proof stopped `apply_patch` on attempt 4 with limit 3.

`guard-event-validation.txt` confirms all expected guard events were present.
The review-loop budget event stores cumulative cost as `total_cost_usd`, so
`agentguard report` counts only per-iteration costs and reports `$0.0510`.

## Artifacts

- `checkout_doctor_trace.jsonl`
- `checkout_demo_trace.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `checkout-demo-report.out.txt`
- `checkout-demo-incident.out.txt`
- `review-loop-report.out.txt`
- `review-loop-incident.out.txt`
- `guard-event-validation.txt`

## Environment health

The installed `agentguard` entry point still fails before command execution because the worker user-site points at a stale editable checkout with malformed `agentguard47` metadata. This is not counted as guard proof. The active checkout path succeeds with `PYTHONPATH=sdk` and `PYTHONNOUSERSITE=1`.

## Validation

- Dependency-free Python 3.11 validation loaded `examples/coding_agent_review_loop.py`, ran it in a temp directory, confirmed the budget guard event uses `total_cost_usd`, and confirmed `summarize_trace` reports `$0.0510`.
- `python -m ruff check examples/coding_agent_review_loop.py sdk/tests/test_coding_agent_review_loop_example.py`
- `git diff --check`
- Python 3.13 `pytest` is blocked in this worker by the same corrupt user-site package metadata captured above; Python 3.11 imports the checkout cleanly but does not have pytest installed. CI should run the new pytest regression in a clean environment.

## Result

Dogfood enforcement is real for this checkout. The local installed-entrypoint environment remains unhealthy and should stay tracked separately from SDK runtime behavior.
