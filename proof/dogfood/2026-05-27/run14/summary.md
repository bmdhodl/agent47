# AgentGuard dogfood proof - 2026-05-27 run14

## Purpose

Run the SDK against its own repo with local AgentGuard enforcement enabled and
leave durable proof that real guard behavior occurred.

## Repo state

- Branch: `dogfood-2026-05-27-run9-worker`
- Base proof PR: `#529`
- Starting commit: `df41ddb`
- Roadmap staleness check: `3 weeks ago`
- Architecture staleness check: `4 weeks ago`
- Existing staleness tracker: issue `#473`

## Commands run

- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli doctor`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli demo`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py examples/coding_agent_review_loop.py`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli incident proof/dogfood/2026-05-27/run14/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli incident proof/dogfood/2026-05-27/run14/agentguard_demo_traces.jsonl`
- `PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli report proof/dogfood/2026-05-27/run14/agentguard_demo_traces.jsonl`

All command exits were `0`.

## Guard behavior observed

Demo trace:

- `guard.budget_warning`: cost reached `$0.84` of `$1.00`.
- `guard.budget_exceeded`: cost reached `$1.08` and was stopped.
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})` was stopped after 3 repeats.
- `guard.retry_limit_exceeded`: `fetch_docs` was stopped after 3 attempts with a limit of 2.

Coding-agent review-loop trace:

- `guard.budget_exceeded`: review attempt 3 pushed cumulative cost to `$0.0510`, over the `$0.0450` limit.
- `guard.retry_limit_exceeded`: `apply_patch` retry attempt 4 exceeded the limit of 3.

## Enforcement verdict

Real enforcement observed. This run is not just command success: the raw JSONL
traces contain guard events for budget, loop, and retry enforcement, and the
review-loop example stopped on both budget and retry limits.

## Artifacts

- `agentguard_demo_traces.jsonl` - raw demo trace.
- `coding_agent_review_loop_traces.jsonl` - raw review-loop trace.
- `demo-incident.md` - local incident output for demo enforcement.
- `review-loop-incident.md` - local incident output for review-loop enforcement.
- `demo-report.log` - local report output for demo enforcement.
- `guard-event-validation.log` - parsed guard-event counts.
- `pr-529-after-wait.json` - PR state after CI/review wait.
- `pr-529-review-threads.json` - review-thread query result.
- `agentguard-*.log`, `checkout-*.log`, `review-loop.log` - command output.

## Validation

- Guard-event parser passed with 4 demo guard events and 2 review-loop guard events.
- Focused pytest passed: `30 passed in 1.31s`.
- `py scripts/sdk_release_guard.py --check-mcp-npm` passed.
- `git diff --check -- proof/dogfood/2026-05-27/run14` passed.
- Artifact hygiene passed: no UTF-8 BOMs, NUL bytes, or local machine paths.
- Post-wait PR review-thread query found 1 thread, 0 unresolved.
