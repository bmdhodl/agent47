# Dogfood proof - 2026-05-28 run16

## Scope

This run stayed SDK-only. It did not touch dashboard, auth, billing, secrets,
deployments, paid-feature code, or SDK runtime behavior.

The active checkout was bound with `PYTHONPATH=./sdk`, and
`import_binding.txt` confirms `agentguard` resolved to this worktree.

## Commands

See `command_status.txt` for the command list and validation status.

Proof commands covered:

- Installed CLI smoke: `agentguard doctor`, `agentguard demo`, `agentguard report`,
  and `agentguard incident`.
- Repo-local proof: `python -m agentguard.cli doctor`, `demo`, `report`, and
  `incident` with `PYTHONPATH=./sdk`.
- Coding-agent proof: `examples/coding_agent_review_loop.py` plus report and
  incident rendering.

## Guard behavior observed

Trace inspection is saved in `trace_inspection.txt`.

Repo-local `demo_trace.jsonl` emitted:

- `guard.budget_warning` at cost used `0.84` against limit `1.0`.
- `guard.budget_exceeded` at cost used `1.08` against limit `1.0`.
- `guard.loop_detected` for repeated `tool.search` calls.
- `guard.retry_limit_exceeded` for `fetch_docs` at retry limit `2`.

Repo-local `coding_agent_review_loop_traces.jsonl` emitted:

- `guard.budget_exceeded` on review attempt `3` at cost `0.051` against limit
  `0.045`.
- `guard.retry_limit_exceeded` for `apply_patch` on attempt `4` against limit
  `3`.

Installed CLI smoke emitted the same demo guard event names.

## Enforcement verdict

Enforcement was real. This run is not just command success: the raw traces
contain concrete budget, loop, and retry guard events, and the rendered reports
and incident files reflect those events.

## Repo and distribution status

- GitHub release: `v1.2.10`.
- PyPI `agentguard47`: `1.2.10`.
- Local SDK: `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Local MCP metadata: `0.2.2`.
- Glama API tool count: `0`.
- Direct MCP Registry server endpoint returned `404`.

## Validation

- Focused proof tests passed: `30 passed in 1.39s`.
- Release guard passed: `python scripts/sdk_release_guard.py --check-mcp-npm`.
- Artifact parse and hygiene checks were run after this summary was written.

## GitHub artifacts

- Rolling dogfood issue: `https://github.com/bmdhodl/agent47/issues/490`.
- Stale ops issue: `https://github.com/bmdhodl/agent47/issues/473`.
- Existing active dogfood PR snapshot: `https://github.com/bmdhodl/agent47/pull/542`.
