# AgentGuard dogfood proof - 2026-05-27 run15

## Purpose

Run the SDK against its own repo with local AgentGuard enforcement enabled and
leave durable proof that real guard behavior occurred.

## Repo state

- Branch: dogfood-2026-05-27-run9-worker
- Base proof PR: #529
- Starting commit: d079936
- Roadmap staleness check: 3 weeks ago
- Architecture staleness check: 4 weeks ago
- Existing staleness tracker: issue #473

## Commands run

- agentguard doctor --trace-file proof/dogfood/2026-05-27/run15/agentguard_doctor_trace.jsonl
- agentguard demo --trace-file proof/dogfood/2026-05-27/run15/agentguard_demo_traces.jsonl
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run15/checkout_agentguard_doctor_trace.jsonl
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run15/checkout_agentguard_demo_traces.jsonl
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py examples/coding_agent_review_loop.py
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli incident proof/dogfood/2026-05-27/run15/coding_agent_review_loop_traces.jsonl
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli incident proof/dogfood/2026-05-27/run15/agentguard_demo_traces.jsonl
- PYTHONPATH=sdk PYTHONNOUSERSITE=1 py -m agentguard.cli report proof/dogfood/2026-05-27/run15/agentguard_demo_traces.jsonl

All command exits were 0.

## Guard behavior observed

Demo trace:

- guard.budget_warning: cost reached 0.84 of 1.00 USD.
- guard.budget_exceeded: cost reached 1.08 USD and was stopped.
- guard.loop_detected: repeated tool.search({"query":"python asyncio"}) was stopped after 3 repeats.
- guard.retry_limit_exceeded: fetch_docs was stopped after 3 attempts with a limit of 2.

Coding-agent review-loop trace:

- guard.budget_exceeded: review attempt 3 pushed cumulative cost to 0.0510 USD, over the 0.0450 USD limit.
- guard.retry_limit_exceeded: apply_patch retry attempt 4 exceeded the limit of 3.

## Enforcement verdict

Real enforcement observed. This run is not just command success: the raw JSONL
traces contain guard events for budget, loop, and retry enforcement, and the
review-loop example stopped on both budget and retry limits.

## Artifacts

- agentguard_doctor_trace.jsonl - installed doctor trace.
- agentguard_demo_traces.jsonl - raw installed demo trace.
- checkout_agentguard_doctor_trace.jsonl - checkout-bound doctor trace.
- checkout_agentguard_demo_traces.jsonl - raw checkout-bound demo trace.
- coding_agent_review_loop_traces.jsonl - raw review-loop trace.
- demo-incident.md - local incident output for demo enforcement.
- review-loop-incident.md - local incident output for review-loop enforcement.
- demo-report.log - local report output for demo enforcement.
- guard-event-validation.log - parsed guard-event counts.
- release-health.log - GitHub release, PyPI, and npm package snapshot.
- agentguard-*.log, checkout-*.log, review-loop.log - command output.

## Validation

- Guard-event parser passed with demo budget/loop/retry guard events and review-loop budget/retry guard events.
- Focused pytest passed with PYTHONPATH=sdk and user-site pytest: 30 passed.
- py scripts/sdk_release_guard.py --check-mcp-npm passed.
- git diff --check -- proof/dogfood/2026-05-27/run15 passed.
- Artifact hygiene passed: no UTF-8 BOMs, NUL bytes, or local machine paths.