# AgentGuard Dogfood Proof - 2026-05-28 run5

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-28/run5/installed-doctor-trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-28/run5/installed-demo-trace.jsonl`
- PowerShell set `$env:PYTHONPATH='./sdk'` before the repo-local commands below.
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-28/run5/repo-doctor-trace.jsonl`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-28/run5/repo-demo-trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report proof/dogfood/2026-05-28/run5/repo-demo-trace.jsonl`
- `python -m agentguard.cli incident proof/dogfood/2026-05-28/run5/review-loop-trace.jsonl`

## Guard behavior observed

- `agentguard demo` emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- The checkout-bound demo report counted 36 total events, 6 spans, 30 events, and 4 guard events.
- The coding-agent review loop stopped on BudgetGuard at `$0.0510 > $0.0450`.
- The same review-loop proof stopped RetryGuard on `apply_patch` attempt 4 with a limit of 3.
- `agentguard incident` classified the review-loop trace as `Status: incident`, `Severity: critical`, `Primary cause: retry_limit_exceeded`.

## Enforcement verdict

Real enforcement observed. This run counts as dogfood proof because raw traces and incident/report output show concrete guard stops, not only successful command execution.

## Artifact inventory

- `commands.log` - exact command transcript.
- `installed-doctor-trace.jsonl` and `installed-demo-trace.jsonl` - PATH CLI proof.
- `repo-doctor-trace.jsonl` and `repo-demo-trace.jsonl` - checkout-bound proof.
- `review-loop-trace.jsonl` - coding-agent review-loop proof.
- `repo-demo-report.txt` - parsed demo report.
- `review-loop-incident.md` - incident report.
- `guard_events.json` and `trace_inspection.txt` - parsed verification artifacts.
