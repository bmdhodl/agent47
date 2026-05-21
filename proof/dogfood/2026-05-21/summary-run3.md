# AgentGuard Dogfood Proof - 2026-05-21 Run 3

## Scope

Recurring dogfood operator run from the local `agent47` checkout on branch `codex/dogfood-proof-2026-05-21-run3`.

Repo identity:

- `git rev-parse HEAD` -> `a2d9cce2fa8096d469fafcc8a4de1dac056d3166`
- `git log -1 --oneline` -> `a2d9cce harden: add actionlint workflow guardrail (#489)`
- `python -c "import agentguard; print(agentguard.__file__)"` -> `<repo>\sdk\agentguard\__init__.py`

## Commands Run

- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts\sdk_release_guard.py --check-mcp-npm`

## Guard Events Observed

Demo trace guard events:

- `guard.budget_warning` with `cost_used=0.84`, `limit_usd=1.0`
- `guard.budget_exceeded` with `cost_used=1.08`, `limit_usd=1.0`
- `guard.loop_detected` for repeated `search`
- `guard.retry_limit_exceeded` for `fetch_docs` at 3 attempts with limit 2

Coding-agent review-loop guard events:

- `guard.budget_exceeded` on attempt 3 with `cost_usd=0.051`, above the `$0.0450` limit
- `guard.retry_limit_exceeded` for `apply_patch` on attempt 4 with limit 3

## Enforcement Verdict

Real enforcement confirmed. The proof includes raw JSONL events showing budget, loop, and retry guards emitted enforcement events. The coding-agent review loop stopped on both budget overrun and retry storm behavior using the repo's offline simulated proof flow, without API keys or dashboard access.

## Validation

- Focused pytest slice: `35 passed in 1.57s`
- Release/package guard: `Release guard passed.`

## Artifacts

- `proof/dogfood/2026-05-21/agentguard_doctor_trace-run3.jsonl`
- `proof/dogfood/2026-05-21/agentguard_demo_traces-run3.jsonl`
- `proof/dogfood/2026-05-21/coding_agent_review_loop_traces-run3.jsonl`
- `proof/dogfood/2026-05-21/agentguard-demo-report-run3.txt`
- `proof/dogfood/2026-05-21/coding-agent-incident-run3.md`
- `proof/dogfood/2026-05-21/summary-run3.md`

## Repo Health Notes

- Roadmap freshness check: `13 days ago`
- Architecture freshness check: `3 weeks ago`
- Existing issue `#473` tracks docs and ops freshness.
