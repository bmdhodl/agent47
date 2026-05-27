# Dogfood proof - 2026-05-27 run7

Branch: `dogfood-2026-05-27-run7-worker`
Base commit: `3f54935`

## Scope

This run stayed SDK-only. It produced fresh proof artifacts for the local
AgentGuard proof path and did not touch dashboard, auth, billing, secrets,
deployments, paid features, or release code.

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-27/run7/installed_doctor_trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-27/run7/installed_demo_trace.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run7/checkout_doctor_trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run7/checkout_demo_trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-27/run7/checkout_demo_trace.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-27/run7/checkout_demo_trace.jsonl`
- `python -m agentguard.cli report proof/dogfood/2026-05-27/run7/review_loop_trace.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-27/run7/review_loop_trace.jsonl`
- temporary venv validation:
  - `agentguard doctor --trace-file proof/dogfood/2026-05-27/run7/venv_installed_doctor_trace.jsonl`
  - `agentguard demo --trace-file proof/dogfood/2026-05-27/run7/venv_installed_demo_trace.jsonl`
  - `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_reporting.py -q`
  - `python -m ruff check examples/coding_agent_review_loop.py sdk/agentguard/demo.py sdk/agentguard/doctor.py sdk/agentguard/reporting.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_reporting.py`
  - `bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`
  - `git diff --check`

## Installed CLI result

The global `agentguard` entry point still fails before executing because this
worker's user-site install points at stale editable metadata from another
checkout. That is environment health evidence only and does not count as guard
proof.

A temporary venv installed from this checkout did run the package entry point
successfully. `venv_installed_demo_trace.jsonl` emitted the same guard behavior
as the checkout-bound demo.

## Concrete guard behavior observed

Parsed source: `guard-events.json`.

### Checkout demo

Trace: `checkout_demo_trace.jsonl`

- `guard.budget_warning`: 1 event at `cost_used=0.84` of `limit_usd=1.0`
- `guard.budget_exceeded`: 1 event at `cost_used=1.08` over `limit_usd=1.0`
- `guard.loop_detected`: 1 event for repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: 1 event for `fetch_docs` attempt 3 with limit 2

### Coding-agent review loop

Trace: `review_loop_trace.jsonl`

- `guard.budget_exceeded`: 1 event on attempt 3 at `tokens_used=12300` and `cost_usd=0.051`
- `guard.retry_limit_exceeded`: 1 event for `apply_patch` attempt 4 with limit 3

The raw guard event is the enforcement proof for the review loop. The current
`main` report output still double-counts review-loop cost as `$0.1020`; the
pending proof/fix PR queue already tracks the corrected cumulative cost field.

## Validation

- Guard-event validation passed for all expected demo and review-loop guard events.
- Focused pytest passed: `38 passed in 1.06s`.
- Focused ruff passed: `All checks passed!`.
- Bandit passed with the repo security skip list.
- `git diff --check` passed.

## Artifacts

- Raw traces:
  - `checkout_doctor_trace.jsonl`
  - `checkout_demo_trace.jsonl`
  - `review_loop_trace.jsonl`
  - `venv_installed_doctor_trace.jsonl`
  - `venv_installed_demo_trace.jsonl`
- Reports and incidents:
  - `demo-report.md`
  - `demo-incident.md`
  - `review-loop-report.md`
  - `review-loop-incident.md`
- Parsed proof:
  - `guard-events.json`
  - `guard-event-validation.log`
- Repo health evidence:
  - `repo-health.md`
  - `open-prs.json`
  - `open-issues.json`
  - `review-thread-summary.log`
  - `github-release.json`
  - `pypi-version.txt`
  - `npm-mcp-version.txt`
  - `mcp-registry-search.json`
  - `glama-api.json`
