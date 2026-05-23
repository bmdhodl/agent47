# AgentGuard Dogfood Proof - 2026-05-23 run3

## Result

Status: pass. Enforcement was real and trace-backed.

This run used the PR #506 branch tip from this checkout, with repo-local imports forced through:

`PYTHONPATH=C:\Users\patri\.codex\worktrees\ec16\agent47\sdk`

Repo-local import resolved to:

`C:\Users\patri\.codex\worktrees\ec16\agent47\sdk\agentguard\__init__.py`

## Commands Run

- `agentguard doctor`
- `agentguard demo`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `gh pr list --state open --json ...`
- `gh issue list --state open --json ...`
- `gh release view --json tagName,publishedAt,url,isPrerelease,isDraft,name`
- `python -m pip index versions agentguard47`
- `npm view @agentguard47/mcp-server version`

Full command output is saved in `command-output.txt`.

## Guard Events Observed

From `agentguard_demo_traces.jsonl`:

- `guard.budget_warning`: cost used `0.84`, limit `1.0`
- `guard.budget_exceeded`: `Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)`
- `guard.loop_detected`: repeated `tool.search({"query":"python asyncio"})` 3 times in the last 6 calls
- `guard.retry_limit_exceeded`: `fetch_docs` attempted 3 times with limit 2

From `coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: attempt 3, `Cost budget exceeded: $0.0510 > $0.0450 (this call added $0.0205)`, `tokens_used=12300`
- `guard.retry_limit_exceeded`: `apply_patch` attempt 4 with limit 3

Trace inspection is saved in `trace-inspection.txt` and `trace-inspection.json`.

## Raw Artifacts

- `agentguard_doctor_trace.jsonl`
- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `demo-report.txt`
- `demo-incident.txt`
- `review-loop-incident.txt`
- `trace-inspection.txt`
- `trace-inspection.json`
- `command-output.txt`

## Validation

- Focused proof and metadata tests: `35 passed in 1.64s`
- Release guard: `Release guard passed.`

## Repo Health Snapshot

- PR #506 is open, green from the prior push, and still `REVIEW_REQUIRED` / `BLOCKED` before this run's push.
- Open PR review-thread sweep found 0 unresolved threads across open PRs.
- Latest GitHub release is `v1.2.10`, published 2026-05-02.
- PyPI latest is `agentguard47 1.2.10`; local `sdk/pyproject.toml` is `1.2.10`.
- npm latest for `@agentguard47/mcp-server` is `0.2.2`; local `mcp-server/package.json` and `server.json` are `0.2.2`.
- Official MCP Registry search still includes `0.2.1` and not `0.2.2`.
- Glama server id `y6zuc6wgtu` still reports `tools_count: 0` from the public API.

## Files in This Run

- `open-prs.json`
- `open-pr-review-threads.json`
- `pr-506-state.json`
- `open-issues.json`
- `github-release.json`
- `package-version-check.json`
- `mcp-registry-search.json`
- `glama-server.json`
- `distribution-inspection.txt`
