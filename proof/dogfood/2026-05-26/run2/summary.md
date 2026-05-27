# AgentGuard Dogfood Proof - 2026-05-26 run2

## Scope

SDK-only recurring dogfood run from the public AgentGuard checkout.

- Repo: `https://github.com/bmdhodl/agent47`
- Commit tested: `a2d9cce2fa8096d469fafcc8a4de1dac056d3166`
- Local run time: `2026-05-26T21:44:35-05:00`
- Runtime proof path: editable install from this checkout, installed CLI, repo-local CLI, and `examples/coding_agent_review_loop.py`

No dashboard, auth, billing, secrets, deployments, paid features, or release changes were touched.

## Commands

All command output is captured in sibling `*.stdout.txt` / `*.stderr.txt` files.

```text
python -m pip install -e ./sdk
agentguard doctor --trace-file proof\dogfood\2026-05-26\run2\installed_agentguard_doctor_trace.jsonl
agentguard demo --trace-file proof\dogfood\2026-05-26\run2\installed_agentguard_demo_traces.jsonl
python -m agentguard.cli doctor --trace-file proof\dogfood\2026-05-26\run2\repo_agentguard_doctor_trace.jsonl
python -m agentguard.cli demo --trace-file proof\dogfood\2026-05-26\run2\repo_agentguard_demo_traces.jsonl
python <repo>\examples\coding_agent_review_loop.py
agentguard report proof\dogfood\2026-05-26\run2\coding_agent_review_loop_traces.jsonl
agentguard incident proof\dogfood\2026-05-26\run2\coding_agent_review_loop_traces.jsonl
agentguard report proof\dogfood\2026-05-26\run2\repo_agentguard_demo_traces.jsonl
agentguard incident proof\dogfood\2026-05-26\run2\repo_agentguard_demo_traces.jsonl
python -m pytest sdk/tests/test_doctor.py sdk/tests/test_demo.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py::test_coding_agent_review_loop_example_runs_offline sdk/tests/test_example_starters.py::test_coding_agent_review_loop_sample_incident_is_in_sync -q
```

Every command exited `0`; see `command-status.txt`.

## Guard Behavior Observed

Enforcement was real. The run produced guard events from both the installed CLI path and the repo-local path.

Installed `agentguard demo` trace:

- `guard.budget_warning`: cost used `0.84`, limit `1.0`
- `guard.budget_exceeded`: cost used `1.08`, limit `1.0`, message `Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)`
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Repo-local `python -m agentguard.cli demo` trace:

- `guard.budget_warning`: cost used `0.84`, limit `1.0`
- `guard.budget_exceeded`: cost used `1.08`, limit `1.0`, message `Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)`
- `guard.loop_detected`: `tool.search({"query":"python asyncio"})` repeated 3 times in the last 6 calls
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

Repo-local coding-agent review-loop trace:

- `guard.budget_exceeded`: attempt 3, cost used `0.051`, token count `12300`, message `Cost budget exceeded: $0.0510 > $0.0450 (this call added $0.0205)`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 with limit 3

Doctor traces also emitted `doctor.verify` events for installed and repo-local paths.

The extracted guard-event ledger is saved as `guard_events.json`.

## Repo Health Snapshot

- Open PRs: 26. PR `#516`, `#510`, `#509`, and older proof PRs are green but still `REVIEW_REQUIRED`.
- PR `#508` remains the highest-signal PR blocker: CI has failed/cancelled Python jobs. Existing comments identify the needed low-risk fix as updating the setup-go guardrail expectation to the pinned v6.4.0 action string.
- Open issues: 15. Issue `#490` remains the rolling dogfood proof log.
- Release/distribution: GitHub release `v1.2.10`, PyPI `agentguard47` `1.2.10`, and npm `@agentguard47/mcp-server` `0.2.2` are aligned.
- Distribution drift still exists outside SDK runtime code: MCP Registry search reports `0.2.1`, and Glama API returns `tools: []`.
- Ops docs are stale by the repo contract: roadmap last changed 3 weeks ago, architecture last changed 4 weeks ago. Issue `#473` already tracks docs refresh.

Raw snapshots are saved in `open-prs.json`, `open-issues.json`, `github-release.json`, `pypi-agentguard47.txt`, `npm-mcp-server.txt`, `mcp-registry-agentguard-search.json`, and `glama-agent47.json`.

## Validation

- Focused tests passed: `23 passed` in `focused-tests.stdout.txt`.
- JSON/JSONL proof files parsed successfully.
- Artifact hygiene passed after normalization: no UTF-16/BOM files, no NUL bytes, and no local checkout path leaks.

## Next Action

Fix PR `#508` by updating the CI guardrail expectation for the pinned `actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`, then rerun CI. This unblocks a real dependency PR without changing SDK runtime behavior.
