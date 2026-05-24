# AgentGuard Dogfood Proof - 2026-05-24 run13



## Goal

Keep one real SDK dogfood workflow running under AgentGuard and leave a durable repo + GitHub proof trail.



## Commands run

- where.exe agentguard

- python import checks with ambient import and with PYTHONPATH=./sdk

- agentguard doctor

- agentguard demo

- PYTHONPATH=./sdk python -m agentguard.cli doctor

- PYTHONPATH=./sdk python -m agentguard.cli demo

- PYTHONPATH=./sdk python examples/coding_agent_review_loop.py

- PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl

- PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl

- focused proof/CLI/metadata pytest slice

- python scripts/sdk_release_guard.py --check-mcp-npm

- GitHub/PyPI/npm/MCP Registry/Glama snapshot commands saved in this folder



## Guard behavior observed

- doctor.verify: 4 span records across installed/repo-local doctor traces.

- guard.budget_warning: 2 event(s). Demo warned at about 84 percent of the budget.

- guard.budget_exceeded: 3 event(s). Demo stopped at USD 1.0800 > USD 1.0000; review loop stopped at USD 0.0510 > USD 0.0450.

- guard.loop_detected: 2 event(s). Demo stopped repeated tool.search calls.

- guard.retry_limit_exceeded: 3 event(s). Demo stopped fetch_docs attempt 3 with limit 2; review loop stopped apply_patch attempt 4 with limit 3.



## Enforcement verdict

Real enforcement observed. This run counts because trace files and incident/report output include concrete guard events, not just successful command exits.



## Package and distribution snapshot

- GitHub release: v1.2.10.

- Local SDK version: 1.2.10.

- PyPI latest: 1.2.10.

- npm MCP package: 0.2.2.

- Local MCP metadata: 0.2.2.

- Official MCP Registry search still reports 0.2.1.

- Glama API still returns an empty tools array.



## Validation

- Focused proof/CLI/metadata tests: 35 passed.

- Release guard with MCP npm check: passed.

- git diff --check: passed.



## Files to inspect

- repo_doctor_trace.jsonl

- repo_demo_traces.jsonl

- review_loop_traces.jsonl

- guard_events.json

- trace_inspection.txt

- repo_demo_report.txt

- review_loop_incident.md
