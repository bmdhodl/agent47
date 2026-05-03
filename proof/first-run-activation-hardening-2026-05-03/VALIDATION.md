# First-Run Activation Hardening Validation

Date: 2026-05-03
Branch: `codex/first-run-activation-hardening`

## Goal

Make the local first-run path recoverable on environments where `pip install`
places the `agentguard` console script outside `PATH`.

## Reproduced Friction

Editable install on this Windows host emitted:

```text
WARNING: The script agentguard.exe is installed in
'C:\Users\patri\AppData\Roaming\Python\Python313\Scripts' which is not on PATH.
```

Without a fallback, a new user can install the SDK successfully but fail at the
next documented `agentguard doctor` command.

## Runtime Proof

Clean temp directory:

```text
C:\Users\patri\AppData\Local\Temp\agentguard-first-run-proof-073756dc4c83460b9fc8f2a224d2503a
```

Commands:

```powershell
python -m pip install -e .\sdk
python -m agentguard.cli doctor
python -m agentguard.cli demo
python -m agentguard.cli quickstart --framework raw --write
python .\agentguard_raw_quickstart.py
python -m agentguard.cli report .agentguard\traces.jsonl
```

Observed fallback guidance:

```text
If 'agentguard' is not on PATH:
  python -m agentguard.cli demo
  python -m agentguard.cli report agentguard_doctor_trace.jsonl

If 'agentguard' is not on PATH:
  python -m agentguard.cli report agentguard_demo_traces.jsonl
  python -m agentguard.cli incident agentguard_demo_traces.jsonl
  python -m agentguard.cli quickstart --framework raw --write

Wrote starter: agentguard_raw_quickstart.py
If 'agentguard' is not on PATH:
  python -m agentguard.cli doctor
  python -m agentguard.cli report .agentguard/traces.jsonl
```

Generated starter result:

```text
Traces saved to .agentguard/traces.jsonl
```

Report result:

```text
AgentGuard report
  Total events: 7
  Spans: 4  Events: 2
  Approx run time: 1.5 ms
  Reasoning steps: 0
  Tool results: 1
  LLM results: 0
  Estimated cost: $0.00
```

## Local Checks

```text
python -m pytest sdk\tests\test_doctor.py sdk\tests\test_demo.py sdk\tests\test_quickstart.py -v
23 passed in 0.23s

python -m ruff check sdk\agentguard\doctor.py sdk\agentguard\demo.py sdk\agentguard\quickstart.py sdk\tests\test_doctor.py sdk\tests\test_demo.py sdk\tests\test_quickstart.py
All checks passed!

python scripts\sdk_preflight.py
All checks passed!

git diff --check
passed
```

## Risk

Low. The change is human-readable CLI guidance only. JSON payloads, public APIs,
runtime guard behavior, package metadata, and dependencies are unchanged.
