# Dogfood proof - 2026-05-22 run4

## Scope

- Repo: `bmdhodl/agent47`
- Branch: `codex/dogfood-proof-2026-05-22-run4`
- SDK path pinned with `PYTHONPATH=./sdk`
- Repo-local import confirmed from `sdk/agentguard/__init__.py`
- No dashboard, auth, billing, secrets, deployments, paid features, or release work.

## Commands run

```powershell
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

## Raw artifacts

- `repo-import.txt`
- `agentguard-doctor.txt`
- `python-doctor.txt`
- `demo-output.txt`
- `coding-agent-review-loop-output.txt`
- `agentguard-demo-report.txt`
- `coding-agent-review-loop-incident.txt`
- `agentguard_doctor_trace-run4.jsonl`
- `agentguard_demo_traces-run4.jsonl`
- `coding_agent_review_loop_traces-run4.jsonl`
- `guard-events-run4.json`

## Guard behavior observed

`agentguard_demo_traces-run4.jsonl` contained 36 events and these guard events:

- `guard.budget_warning`: cost reached `$0.84` of a `$1.00` limit.
- `guard.budget_exceeded`: cost reached `$1.0800 > $1.0000`.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with a limit of 2.

`coding_agent_review_loop_traces-run4.jsonl` contained 14 events and these guard events:

- `guard.budget_exceeded`: review attempt 3 reached `$0.0510 > $0.0450` after 12,300 tokens.
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 exceeded the retry limit of 3.

## Result

Enforcement was real. The run produced trace-level guard events for budget, loop, and retry enforcement in the offline demo, plus budget and retry enforcement in the coding-agent review-loop example.
