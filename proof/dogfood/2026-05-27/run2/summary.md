# AgentGuard Dogfood Proof - 2026-05-27 run2

## Repo

- Checkout: `<repo-root>`
- Branch: `dogfood-2026-05-27-run2-worker`
- Base commit: `a2d9cce2fa8096d469fafcc8a4de1dac056d3166`
- SDK version: `1.2.10`

## Commands Run

```powershell
python -c "import agentguard,sys; print(agentguard.__file__); print(getattr(agentguard,'__version__',None)); print(sys.executable)"
agentguard doctor --trace-file proof/dogfood/2026-05-27/run2/preinstall-doctor-trace.jsonl
python -m pip install -e ./sdk
python -c "import agentguard,sys; print(agentguard.__file__); print(getattr(agentguard,'__version__',None)); print(sys.executable)"
agentguard doctor --trace-file proof/dogfood/2026-05-27/run2/doctor-trace.jsonl
agentguard demo --trace-file proof/dogfood/2026-05-27/run2/demo-trace.jsonl
python examples/coding_agent_review_loop.py
agentguard report proof/dogfood/2026-05-27/run2/demo-trace.jsonl
agentguard incident proof/dogfood/2026-05-27/run2/demo-trace.jsonl --format markdown
agentguard report proof/dogfood/2026-05-27/run2/review-loop-trace.jsonl
agentguard incident proof/dogfood/2026-05-27/run2/review-loop-trace.jsonl --format markdown
```

## Fix Applied

This run addressed a live review finding from PR `#518`: the review-loop
example previously stored a cumulative total in `data.cost_usd`, which caused
report and incident rendering to count both per-turn cost events and the
cumulative guard field. The source now records that cumulative guard field as
`total_cost_usd`, and this run regenerated the proof from the fixed example.

## Install Binding

The first import check showed Python was still bound to the previous worker
checkout. This run reinstalled the SDK from the active checkout with
`python -m pip install -e ./sdk`.

Post-install import proof:

```text
<repo-root>\sdk\agentguard\__init__.py
1.2.10
<python-executable>
```

## Guard Behavior Observed

Real enforcement was observed in raw traces, not inferred from command exit
codes.

### `demo-trace.jsonl`

- `guard.budget_warning`: cost reached `$0.84` of a `$1.00` limit.
- `guard.budget_exceeded`: cost reached `$1.08` and exceeded the `$1.00` limit.
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls.
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times against a retry limit of 2.

### `review-loop-trace.jsonl`

- `guard.budget_exceeded`: review loop stopped on attempt 3 after `12300` tokens and `total_cost_usd` of `$0.0510`, exceeding the `$0.0450` limit.
- `guard.retry_limit_exceeded`: `apply_patch` retry storm stopped on attempt 4 against a retry limit of 3.

## Artifacts

- `preinstall-import.txt`
- `preinstall-doctor.txt`
- `preinstall-doctor-trace.jsonl`
- `pip-install-editable.txt`
- `postinstall-import.txt`
- `postfix-import.txt`
- `doctor.txt`
- `doctor-trace.jsonl`
- `demo.txt`
- `demo-trace.jsonl`
- `demo-report.txt`
- `demo-incident.md`
- `review-loop.txt`
- `review-loop-trace.jsonl`
- `review-loop-report.txt`
- `review-loop-incident.md`

## Result

This run counts as dogfood proof. The active checkout produced raw trace events
showing budget, loop, and retry guard behavior, plus local report and incident
outputs from those traces.
