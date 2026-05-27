# AgentGuard Dogfood Proof - 2026-05-27 run3

## Checkout

- Repo: `bmdhodl/agent47`
- Branch: `dogfood-2026-05-27-run3-worker`
- Commit: `3f54935` (`origin/main` at run start)
- Scope: SDK-only dogfood proof, repo health snapshot, and rolling issue update

## Commands Run

Initial package-installed path:

```powershell
python -m pip show agentguard47
agentguard doctor
agentguard demo
python -m pip install -e ./sdk
```

Result: the worker user-site install was corrupt before this run. `pip show`
reported `agentguard47` with `Version: None`, `pip install -e ./sdk` could not
uninstall it because no `RECORD` file existed, and the `agentguard` entry point
imported `<stale-agent47-worktree>/sdk\agentguard`.

Active-checkout proof path:

```powershell
$env:PYTHONPATH=(Resolve-Path 'sdk').Path
python -m agentguard.cli doctor
python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-27/run3/agentguard_demo_traces.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report proof/dogfood/2026-05-27/run3/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-27/run3/coding_agent_review_loop_traces.jsonl
python -m agentguard.cli report proof/dogfood/2026-05-27/run3/agentguard_demo_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-27/run3/agentguard_demo_traces.jsonl
```

Validation:

```powershell
python -m pytest sdk/tests/test_example_starters.py::test_coding_agent_review_loop_example_runs_offline sdk/tests/test_example_starters.py::test_coding_agent_review_loop_sample_incident_is_in_sync sdk/tests/test_doctor.py -q
python -m ruff check examples/coding_agent_review_loop.py sdk/agentguard/cli.py sdk/tests/test_example_starters.py sdk/tests/test_doctor.py
```

## Guard Events Observed

`agentguard_demo_traces.jsonl`:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1
- `guard.loop_detected`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement:

- BudgetGuard warned at `$0.84` and stopped the run at `$1.08 > $1.00`.
- LoopGuard stopped `tool.search({"query":"python asyncio"})` after 3 repeats.
- RetryGuard stopped `fetch_docs` after 3 attempts with a limit of 2.

`coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: 1
- `guard.retry_limit_exceeded`: 1

Concrete enforcement:

- BudgetGuard stopped the review loop on attempt 3 at `$0.0510 > $0.0450`.
- RetryGuard stopped `apply_patch` on attempt 4 with a limit of 3.

## Reports

- `demo-report.txt`
- `demo-incident.md`
- `review-loop-report.txt`
- `review-loop-incident.md`
- `validation-guard-events.txt`

## Repo Health Snapshot

- Roadmap staleness: `ops/03-ROADMAP_NOW_NEXT_LATER.md` last changed 3 weeks ago.
- Architecture staleness: `ops/02-ARCHITECTURE.md` last changed 4 weeks ago.
- Latest GitHub release: `v1.2.10`.
- PyPI `agentguard47`: `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Official MCP Registry still reports `0.2.1`.
- Glama API returned HTTP 403 from this worker, so tool indexing could not be verified here.

## Result

Enforcement was real for the active checkout. The package-installed CLI path is
blocked in this worker by corrupt local Python user-site metadata, not by this
repo's source tree. The successful proof used the active repo via
`PYTHONPATH=sdk` and produced fresh trace, report, and incident artifacts.
