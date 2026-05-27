# AgentGuard Dogfood Run 17 - 2026-05-27

## Scope

SDK-only recurring dogfood pass from PR branch
`dogfood-2026-05-27-run9-worker` in the public AgentGuard repo. No dashboard,
auth, billing, secrets, deployments, paid-feature code, or release cuts were
touched.

The required ops staleness check still reports:

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 3 weeks ago
- `ops/02-ARCHITECTURE.md`: 4 weeks ago

Issue #473 already tracks this ops-cadence gap.

## Commands Run

Installed/global CLI path:

```powershell
agentguard doctor --trace-file proof/dogfood/2026-05-27/run17/agentguard_doctor_trace.jsonl
agentguard demo --trace-file proof/dogfood/2026-05-27/run17/agentguard_demo_traces.jsonl
```

Checkout-bound canonical path:

```powershell
$env:PYTHONPATH = "<repo>/sdk"
$env:PYTHONNOUSERSITE = "1"
py -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-27/run17/checkout_agentguard_doctor_trace.jsonl
py -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run17/checkout_agentguard_demo_traces.jsonl
py -m agentguard.cli report proof/dogfood/2026-05-27/run17/checkout_agentguard_demo_traces.jsonl
py -m agentguard.cli incident proof/dogfood/2026-05-27/run17/checkout_agentguard_demo_traces.jsonl --format markdown
py examples/coding_agent_review_loop.py
py -m agentguard.cli incident proof/dogfood/2026-05-27/run17/coding_agent_review_loop_traces.jsonl --format markdown
```

Health and validation:

```powershell
gh release view v1.2.10 --repo bmdhodl/agent47 --json tagName,name,publishedAt,url
py -m pip index versions agentguard47
npm view @agentguard47/mcp-server version
py scripts/sdk_release_guard.py --check-mcp-npm
C:\Python313\python.exe -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py -q
git diff --check -- proof/dogfood/2026-05-27/run17
```

## Guard Events Observed

`checkout_agentguard_demo_traces.jsonl` emitted:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

`coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Enforcement was real. The offline demo stopped simulated budget overrun, tool
loop, and retry storm behavior. The coding-agent review-loop proof stopped the
review loop at `$0.0510 > $0.0450` and stopped `apply_patch` retry attempt 4
with a retry limit of 3.

## Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `checkout_agentguard_doctor_trace.jsonl`
- `checkout_agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo-incident.md`
- `review-loop-incident.md`
- command logs and exit-code files for each proof/validation command
- `guard-event-validation.log`
- `artifact-hygiene.log`
- `validation-exits.txt`

## Validation Result

- All recorded exit files are `0`.
- Guard-event validation found the expected demo and review-loop guard events.
- Artifact hygiene passed: local paths redacted; no UTF-8 BOM or NUL bytes found.
- Focused pytest passed: `30 passed`.
- `git diff --check -- proof/dogfood/2026-05-27/run17` passed after this summary was added.
- Release/package snapshot: GitHub release `v1.2.10`, PyPI `agentguard47`
  latest `1.2.10`, npm `@agentguard47/mcp-server` latest `0.2.2`.
