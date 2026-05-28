# AgentGuard dogfood proof - 2026-05-28 run4

## Scope

- Repo: `bmdhodl/agent47`
- Branch: `dogfood-2026-05-28-run4-worker`
- SDK version under test: `agentguard47 1.2.10`
- Runtime: local-only, no API keys, no dashboard, no network calls for proof execution

## Commands run

```powershell
agentguard doctor --trace-file proof/dogfood/2026-05-28/run4/agentguard_doctor_trace.jsonl
agentguard demo --trace-file proof/dogfood/2026-05-28/run4/agentguard_demo_traces.jsonl
$env:PYTHONPATH = (Resolve-Path 'sdk').Path
Push-Location proof/dogfood/2026-05-28/run4
python ../../../../examples/coding_agent_review_loop.py
Pop-Location
python -m agentguard.cli report proof/dogfood/2026-05-28/run4/agentguard_demo_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-28/run4/agentguard_demo_traces.jsonl
python -m agentguard.cli report proof/dogfood/2026-05-28/run4/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-28/run4/coding_agent_review_loop_traces.jsonl
```

All command exit codes were `0`; see `command_exit_codes.txt`.

## Raw artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_doctor_output.txt`
- `agentguard_demo_traces.jsonl`
- `agentguard_demo_output.txt`
- `agentguard_demo_report.txt`
- `agentguard_demo_incident.md`
- `coding_agent_review_loop_traces.jsonl`
- `coding_agent_review_loop_output.txt`
- `coding_agent_review_loop_report.txt`
- `coding_agent_review_loop_incident.md`
- `command_exit_codes.txt`

## Guard behavior observed

`agentguard doctor` wrote 4 setup-verification events to `agentguard_doctor_trace.jsonl`.

`agentguard demo` wrote 36 events and emitted these guard events:

- `guard.budget_warning`: cost reached `$0.84` of the `$1.00` limit.
- `guard.budget_exceeded`: cost reached `$1.08 > $1.00`; enforcement stopped the runaway budget path.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the 6-call window.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with a retry limit of 2.

`examples/coding_agent_review_loop.py` wrote 14 events and emitted these guard events:

- `guard.budget_exceeded`: review attempt 3 pushed cost to `$0.0510 > $0.0450`, with 12,300 tokens used.
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 exceeded the retry limit of 3.

## Enforcement verdict

Enforcement was real. The demo path raised and recorded budget, loop, and retry guard stops. The repo-local coding-agent proof stopped the review loop when cost exceeded the configured budget and stopped the patch retry storm at the configured retry ceiling.
