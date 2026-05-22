# AgentGuard Dogfood Proof - 2026-05-22

## Scope

SDK-only recurring dogfood run for the public AgentGuard47 repository.

## Repo Binding

- Repository: `bmdhodl/agent47`
- Checkout: `<repo_root>`
- Head: `a2d9cce2fa8096d469fafcc8a4de1dac056d3166`
- Repo-local import proof: `<repo_root>\sdk\agentguard\__init__.py`
- Python: `3.13.2`
- AgentGuard package version: `1.2.10`

## Commands Run

```powershell
$env:PYTHONPATH = "<repo_root>\sdk"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
```

## Guard Events Observed

`agentguard_demo_traces.jsonl`:

- `guard.budget_warning`: 1 event at `$0.84` used against `$1.00` limit.
- `guard.budget_exceeded`: 1 event at `$1.08` used against `$1.00` limit.
- `guard.loop_detected`: 1 event for repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: 1 event for `fetch_docs` attempt 3 with limit 2.

`coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: 1 event on review attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: 1 event for `apply_patch` attempt 4 with limit 3.

## Enforcement Verdict

Real enforcement observed. This run is trace-backed, not stdout-only: budget, loop, and retry guards emitted concrete guard events in JSONL traces, and the coding-agent review-loop example stopped on local budget and retry limits without API keys, dashboard access, or network calls.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `agentguard_demo_report.txt`
- `coding_agent_review_loop_incident.md`
