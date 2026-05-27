# AgentGuard dogfood run 20

Date: 2026-05-27
Branch: `dogfood-2026-05-27-run9-worker`
Base proof sink: PR #529 and issue #490

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-27/run20/installed_doctor_trace.jsonl`
- `agentguard demo --trace-file proof/dogfood/2026-05-27/run20/installed_demo_traces.jsonl`
- `PYTHONPATH=./sdk PYTHONNOUSERSITE=1 python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run20/checkout_doctor_trace.jsonl`
- `PYTHONPATH=./sdk PYTHONNOUSERSITE=1 python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run20/checkout_demo_traces.jsonl`
- `PYTHONPATH=./sdk PYTHONNOUSERSITE=1 python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk PYTHONNOUSERSITE=1 python -m agentguard.cli report proof/dogfood/2026-05-27/run20/checkout_demo_traces.jsonl`
- `PYTHONPATH=./sdk PYTHONNOUSERSITE=1 python -m agentguard.cli incident proof/dogfood/2026-05-27/run20/review_loop_traces.jsonl`
- `py -3.11 -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `py -3.11 scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

The run produced real AgentGuard enforcement evidence in raw JSONL traces.

Installed demo trace:

- `guard.budget_warning`: cost used `0.84`, limit USD `1.0`
- `guard.budget_exceeded`: cost used `1.08`, limit USD `1.0`
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the 6-call window
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Checkout-bound demo trace:

- `guard.budget_warning`: cost used `0.84`, limit USD `1.0`
- `guard.budget_exceeded`: cost used `1.08`, limit USD `1.0`
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the 6-call window
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Coding-agent review-loop trace:

- `guard.budget_exceeded`: attempt 3 stopped at USD `0.0510 > 0.0450`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 exceeded limit 3

Enforcement was real. The proof is not based only on command success; `trace_inspection.txt` parsed the JSONL files and confirmed the required guard events were present with no missing demo or review-loop events.

## Validation

- Focused proof pytest: `35 passed in 1.02s`
- Release guard MCP npm check: passed
- Artifact hygiene: UTF-8 decodable, no BOM, no NUL bytes, no exact local checkout path
- Package snapshot: local SDK `1.2.10`, PyPI `agentguard47` latest `1.2.10`, local/npm MCP `0.2.2`

## Files in this bundle

- `installed_doctor_trace.jsonl`
- `installed_demo_traces.jsonl`
- `checkout_doctor_trace.jsonl`
- `checkout_demo_traces.jsonl`
- `review_loop_traces.jsonl`
- `report.log`
- `incident.log`
- `guard_events.json`
- `trace_inspection.txt`
- `artifact_hygiene.txt`
- command logs and exit-code files
