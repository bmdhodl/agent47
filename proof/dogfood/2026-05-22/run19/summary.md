# AgentGuard Dogfood Proof - 2026-05-22 Run 19

## Scope

- Repo: `bmdhodl/agent47`
- Branch target: `codex/dogfood-proof-2026-05-22-run11`
- SDK scope only. No dashboard, auth, billing, secrets, deployments, paid features, or release work.
- Local import binding: `<repo_root>/sdk/agentguard/__init__.py`

## Commands Run

```powershell
python -m pip install -e .\sdk
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

## Guard Behavior Observed

The run produced real guard enforcement in raw trace output, not just successful command exits.

Demo trace:

- `guard.budget_warning`: cost used `0.84` against limit `1.0`
- `guard.budget_exceeded`: cost used `1.08` against limit `1.0`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})`
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Coding-agent review loop trace:

- `guard.budget_exceeded`: attempt 3, `12300` tokens, `$0.0510 > $0.0450`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 with limit 3

## Artifacts

- `agentguard_demo_traces.jsonl`: raw demo trace
- `coding_agent_review_loop_traces.jsonl`: raw coding-agent review-loop trace
- `guard_events.json`: extracted guard-event payloads
- `demo_report.txt`: local report output for the demo trace
- `review_loop_incident.txt`: local incident output for the review-loop trace
- `agentguard_doctor.txt` and `python_doctor.txt`: CLI doctor outputs
- `demo_stdout.txt` and `review_loop_stdout.txt`: command stdout captures

## Result

Enforcement was real. The demo stopped budget overrun, a repeated tool loop, and a retry storm. The coding-agent review-loop proof stopped a budget overrun on review attempt 3 and stopped repeated `apply_patch` retries on attempt 4.
