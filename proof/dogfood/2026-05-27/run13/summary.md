# AgentGuard dogfood run 13 - 2026-05-27

## Repo state

- Repo: `https://github.com/bmdhodl/agent47.git`
- PR branch updated: `dogfood-2026-05-27-run9-worker`
- Base commit before this proof: `ba13c30d3d701bf1fe42e48191c2c02be36c014f`
- Scope: SDK-only dogfood proof artifacts. No runtime SDK, dashboard, auth, billing, secret, deployment, or paid-feature files changed.

## Commands run

```powershell
agentguard doctor
agentguard demo
$env:PYTHONPATH='sdk'; $env:PYTHONNOUSERSITE='1'
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report proof\dogfood\2026-05-27\run13\agentguard_demo_traces.jsonl
python -m agentguard.cli incident proof\dogfood\2026-05-27\run13\agentguard_demo_traces.jsonl
python -m agentguard.cli report proof\dogfood\2026-05-27\run13\coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof\dogfood\2026-05-27\run13\coding_agent_review_loop_traces.jsonl
py -m pytest sdk\tests\test_demo.py sdk\tests\test_doctor.py sdk\tests\test_cli_report.py sdk\tests\test_example_starters.py -q
py scripts\sdk_release_guard.py --check-mcp-npm
```

## Guard behavior observed

This run counts as real dogfood proof. Guard behavior was observed in raw traces, CLI output, and incident/report output.

`agentguard demo` trace:

- `guard.budget_warning`: warning fired at `$0.84`, 84% of the `$1.00` demo limit.
- `guard.budget_exceeded`: BudgetGuard stopped the run at `$1.0800 > $1.0000`.
- `guard.loop_detected`: LoopGuard stopped repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: RetryGuard stopped `fetch_docs` after 3 attempts with limit 2.

`examples/coding_agent_review_loop.py` trace:

- `guard.budget_exceeded`: BudgetGuard stopped the review loop on attempt 3 at `$0.0510 > $0.0450` after 12,300 tokens.
- `guard.retry_limit_exceeded`: RetryGuard stopped `apply_patch` attempt 4 with limit 3.

Validation parser result:

```text
agentguard_demo_traces.jsonl: 36 events, 4 guard event names
coding_agent_review_loop_traces.jsonl: 14 events, 2 guard event names
guard-event validation passed
artifact hygiene passed
focused pytest: 30 passed
release guard: passed
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

- `agentguard doctor` and `agentguard demo` passed globally and checkout-bound with `PYTHONPATH=sdk` / `PYTHONNOUSERSITE=1`.
- GitHub release is `v1.2.10`; PyPI `agentguard47` latest is `1.2.10`; npm `@agentguard47/mcp-server` latest is `0.2.2`.
- Roadmap is 3 weeks old and architecture is 4 weeks old; issue #473 continues to track this.
- PR #529 and PR #530 have no unresolved review threads and remain blocked by required human review.
- PR #520 has six unresolved release-workflow review threads.

## PRs/issues needing action

- PR #530 is green and review-thread clean; needs human review.
- PR #529 is green as of the previous commit and will need CI/review-thread closeout after this run13 commit lands.
- PR #520 still needs release-workflow review feedback addressed.
- Issue #507 and #469 track dependency/security scanner findings that still need clean SDK-only reproduction before escalation.
- Issue #473 tracks stale roadmap/architecture docs.
- Issue #490 is the rolling dogfood proof log and was updated for this run.

## Next recommended task

Stop adding duplicate proof-only PRs after this branch gets human review; next highest ROI is addressing PR #520 release-workflow feedback or getting human review on PR #529/#530.