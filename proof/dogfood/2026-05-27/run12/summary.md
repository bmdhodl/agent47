# AgentGuard dogfood run 12 - 2026-05-27

## Repo state

- Repo: `https://github.com/bmdhodl/agent47.git`
- Branch used locally: `dogfood-2026-05-27-run12-worker`
- PR branch updated: `dogfood-2026-05-27-run9-worker`
- Base commit for this proof branch: `0a8878740f672d083c3d623f2722655c65d4c500`
- Scope: SDK-only dogfood proof artifacts. No runtime SDK, dashboard, auth, billing, secret, deployment, or paid-feature files changed.

## Commands run

```powershell
agentguard doctor
agentguard demo
$env:PYTHONPATH='sdk'; $env:PYTHONNOUSERSITE='1'
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report proof\dogfood\2026-05-27\run12\agentguard_demo_traces.jsonl
python -m agentguard.cli incident proof\dogfood\2026-05-27\run12\agentguard_demo_traces.jsonl
python -m agentguard.cli report proof\dogfood\2026-05-27\run12\coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof\dogfood\2026-05-27\run12\coding_agent_review_loop_traces.jsonl
```

## Guard behavior observed

This run counts as real dogfood proof. Guard behavior was observed in raw traces, CLI output, and incident/report output.

`agentguard demo` trace:

- `guard.budget_warning`: warning fired at `$0.84`, 84% of the `$1.00` demo limit.
- `guard.budget_exceeded`: BudgetGuard stopped the run at `$1.0800 > $1.0000`.
- `guard.loop_detected`: LoopGuard stopped repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: RetryGuard stopped `fetch_docs` after 3 attempts with limit 2.

`examples/coding_agent_review_loop.py` trace:

- `guard.budget_exceeded`: BudgetGuard stopped the review loop at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: RetryGuard stopped `apply_patch` attempt 4 with limit 3.

Validation parser result:

```text
agentguard_demo_traces.jsonl: 36 events, 4 guard events
coding_agent_review_loop_traces.jsonl: 14 events, 2 guard events
guard-event validation passed
artifact hygiene passed
focused pytest: 21 passed
```

## Artifact files

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard-doctor-global.log`
- `agentguard-demo-global.log`
- `agentguard-doctor-checkout.log`
- `agentguard-demo-checkout.log`
- `coding-agent-review-loop.log`
- `agentguard-demo-report.log`
- `agentguard-demo-incident.md`
- `coding-agent-review-loop-report.log`
- `coding-agent-review-loop-incident.md`
- `guard-event-validation.log`
- `artifact-hygiene.log`
- `focused-pytest.log`

## Repo health snapshot

- `agentguard doctor` and `agentguard demo` both passed globally in this worker, unlike recent stale user-site failures.
- Checkout-bound `python -m agentguard.cli doctor/demo` also passed with `PYTHONPATH=sdk` and `PYTHONNOUSERSITE=1`.
- GitHub release is `v1.2.10`; PyPI `agentguard47` latest is `1.2.10`; npm `@agentguard47/mcp-server` latest is `0.2.2`.
- Roadmap is 3 weeks old and architecture is 4 weeks old; issue #473 continues to track this.
- PR #529 has no unresolved review threads and remains blocked by required human review.

## PRs/issues needing action

- PR #530 is green but has three outdated, unresolved review threads from the previous implementation. It likely needs thread resolution or a final review pass.
- PR #520 still has six active release-workflow review threads.
- Issue #507 and #469 track dependency/security scanner findings.
- Issue #473 tracks stale roadmap/architecture docs.
- Issue #490 is the rolling dogfood proof log and was updated for this run.

## Next recommended task

Resolve/close the outdated review threads on PR #530 if the current diff really addressed them, then get human review on PR #529/#530 before adding more proof-only changes.
