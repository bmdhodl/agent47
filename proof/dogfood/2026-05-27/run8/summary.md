# AgentGuard dogfood run 8 - 2026-05-27

Commit: `3f54935`
Branch: `dogfood-2026-05-27-run8-worker`

## Commands run

```powershell
agentguard doctor
python -m venv $env:TEMP\agentguard-dogfood-run8-venv
$env:TEMP\agentguard-dogfood-run8-venv\Scripts\python.exe -m pip install --upgrade pip
$env:TEMP\agentguard-dogfood-run8-venv\Scripts\python.exe -m pip install -e .\sdk
$env:TEMP\agentguard-dogfood-run8-venv\Scripts\agentguard.exe doctor
$env:TEMP\agentguard-dogfood-run8-venv\Scripts\agentguard.exe demo
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONPATH = ".\sdk"
python examples/coding_agent_review_loop.py
python -m agentguard.cli report coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m agentguard.cli demo
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident agentguard_demo_traces.jsonl
@'...inline Python JSONL guard-event validation...'@ | python -
```

## Guard behavior observed

`agentguard_demo_traces.jsonl` contains 36 events and the expected demo guard events:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

The demo incident report classified the run as `incident`, severity `critical`, primary cause `loop_detected`, with estimated savings of 500 tokens / `$0.1200`.

`coding_agent_review_loop_traces.jsonl` contains 14 events and the expected review-loop guard events:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

The review-loop run stopped the budget path at `$0.0510 > $0.0450` and stopped the retry path when `apply_patch` reached attempt 4 with a limit of 3. The incident report classified the run as `incident`, severity `critical`, primary cause `retry_limit_exceeded`, with estimated savings of `$0.0205`.

`agentguard_doctor_trace.jsonl` contains 4 setup events, including 2 `doctor.verify` events.

## Enforcement conclusion

Enforcement was real. The proof is not just command success: the raw JSONL traces and incident output show AgentGuard emitted budget, loop, and retry guard events and stopped the simulated runaway paths.

## Local environment note

The global `agentguard doctor` smoke check still failed before reaching the active checkout because this worker has stale user-site package metadata. The isolated editable install from `.\sdk` and the explicit checkout-bound `PYTHONNOUSERSITE=1` / `PYTHONPATH=.\sdk` paths succeeded.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo-report.log`
- `demo-incident.log`
- `review-loop-report.log`
- `review-loop-incident.log`
- `guard-event-validation.log`
- `artifact-hygiene.log`
- `venv-agentguard-doctor.log`
- `venv-agentguard-demo.log`
- `local-agentguard-demo.log`
- `global-agentguard-doctor.log`
