# Dogfood Proof - 2026-05-27 run4

Branch: `dogfood-2026-05-27-run4-worker`
Base commit: `3f54935`

## Scope

- SDK-only dogfood proof run.
- Runtime fix: source-checkout imports now tolerate malformed installed package metadata.
- No dashboard, auth, billing, deployment, secret, or paid-feature code touched.

## Commands run

Installed CLI path:

- `agentguard doctor --trace-file proof/dogfood/2026-05-27/run4/installed-doctor-trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-27/run4/installed-demo-trace.jsonl`

Active checkout path:

- `PYTHONPATH=sdk python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run4/repo-doctor-trace.jsonl`
- `PYTHONPATH=sdk python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run4/demo-trace.jsonl`
- `PYTHONPATH=sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=sdk python -m agentguard.cli report proof/dogfood/2026-05-27/run4/demo-trace.jsonl`
- `PYTHONPATH=sdk python -m agentguard.cli incident proof/dogfood/2026-05-27/run4/demo-trace.jsonl`
- `PYTHONPATH=sdk python -m agentguard.cli incident proof/dogfood/2026-05-27/run4/review-loop-trace.jsonl`

Validation:

- `PYTHONPATH=sdk python -m pytest sdk/tests/test_hardening.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_reporting.py -q`
- `PYTHONPATH=sdk python -m ruff check sdk/agentguard/__init__.py sdk/tests/test_hardening.py examples/coding_agent_review_loop.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_reporting.py`
- `PYTHONPATH=sdk python -m pytest sdk/tests/ --cov=agentguard --cov-fail-under=80 -q`
- `PYTHONPATH=sdk python -m pytest sdk/tests/test_architecture.py -q`
- `PYTHONPATH=sdk python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`
- `PYTHONPATH=sdk python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py scripts/ci_tools_requirements_guard.py`
- `PYTHONPATH=sdk python scripts/ci_tools_requirements_guard.py`
- `PYTHONPATH=sdk;scripts python scripts/sdk_release_guard.py --check-mcp-npm`
- `npm --prefix mcp-server ci`
- `npm --prefix mcp-server test`
- `git diff --check`

## Guard behavior observed

Real enforcement was observed in raw trace files and parsed into `guard-events.json`.

Demo trace:

- `guard.budget_warning`: fired at cost used `0.84` of `1.00`.
- `guard.budget_exceeded`: stopped demo at cost used `1.08` over limit `1.00`.
- `guard.loop_detected`: stopped repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: stopped `fetch_docs` attempt 3 with limit 2.

Review-loop trace:

- `guard.budget_exceeded`: stopped the review loop on attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: stopped `apply_patch` attempt 4 with limit 3.

Doctor trace:

- `doctor.verify`: start and end spans were emitted.

## Environment issue and fix

The installed `agentguard` entry point still imports a stale editable checkout and hits malformed user-site metadata:

- `agentguard47` metadata reports `Version: None`.
- The installed entry point imports `<stale-worktree>/sdk/agentguard`.
- Before this run's fix, even active-checkout imports failed when `importlib.metadata.version("agentguard47")` hit that malformed metadata.

This run adds a narrow fallback for malformed package metadata so source-checkout dogfood, tests, and local CLI proof can run even when the worker user-site install is corrupt. The installed entry point itself remains an environment cleanup issue because it still points to the stale checkout.

## Validation result

- Focused pytest: `72 passed in 0.27s`.
- Full SDK pytest with coverage: `770 passed in 14.94s`, coverage `92.74%`.
- Architecture pytest: `9 passed in 0.15s`.
- Bandit security scan: passed.
- Focused ruff and Makefile lint equivalent: `All checks passed!`
- CI tools guard: passed.
- Release guard with MCP npm check: `Release guard passed.`
- MCP npm tests: `10` tests passed after `npm --prefix mcp-server ci`.
- Guard-event validation: demo has 4 guard events, review loop has 2 guard events, doctor has 2 verify events.
- Artifact hygiene: UTF-8 files, no BOM/NUL bytes, JSON/JSONL parseable, local machine paths redacted.

## Repo health snapshot

- Open PRs are mostly green but blocked by required human review.
- PR #508 still has failed/cancelled Python checks on the `actions/setup-go` bump.
- PR #519 already tracks the separate review-loop cost-field cleanup.
- Roadmap is stale by repo threshold: `3 weeks ago`.
- Architecture is stale by repo threshold: `4 weeks ago`.
- GitHub release and PyPI remain `v1.2.10` / `1.2.10`.
- npm MCP remains `0.2.2`; official MCP Registry search still reports `0.2.1`.
- Glama API timed out from this worker, so tool indexing could not be verified in this run.
