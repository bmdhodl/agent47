# AgentGuard dogfood run12 - 2026-05-24

## Goal

Keep the public SDK dogfood loop active by running installed and repo-local
AgentGuard proof paths, confirming real guard enforcement from raw traces, and
publishing a durable repo/GitHub artifact.

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-24/run12/installed-doctor-trace.jsonl --json`
- `agentguard demo --trace-file proof/dogfood/2026-05-24/run12/installed-demo-trace.jsonl`
- `python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run12/repo-local-doctor-trace.jsonl --json`
- `python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run12/repo-local-demo-trace.jsonl`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report <trace>`
- `python -m agentguard.cli incident <trace>`
- `gh pr list --state open --limit 40 --json ...`
- `gh issue list --state open --limit 80 --json ...`
- `gh release view --json tagName,name,publishedAt,url,isPrerelease,isDraft`
- `python -m pip index versions agentguard47`
- `git log -1 --format='%cr' -- ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `git log -1 --format='%cr' -- ops/02-ARCHITECTURE.md`

## Guard behavior observed

Raw trace inspection is saved in `trace_inspection.txt` and parsed events are in
`guard_events.json`.

- Installed and repo-local doctor emitted `doctor.verify` start/end events.
- Installed demo emitted `guard.budget_warning`.
- Installed demo emitted `guard.budget_exceeded`: `Cost budget exceeded: $1.0800 > $1.0000`.
- Installed demo emitted `guard.loop_detected` for repeated `tool.search({"query":"python asyncio"})`.
- Installed demo emitted `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- Repo-local demo emitted the same budget, loop, and retry guard events.
- Coding-agent review loop emitted `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- Coding-agent review loop emitted `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

Enforcement was real: the proof includes explicit stopped demo calls and review
loop stops, not just successful command execution.

## Artifacts

- `installed-doctor-trace.jsonl`
- `installed-demo-trace.jsonl`
- `repo-local-doctor-trace.jsonl`
- `repo-local-demo-trace.jsonl`
- `coding_agent_review_loop_traces.jsonl`
- `guard_events.json`
- `trace_inspection.txt`
- report and incident stdout captures for demo and review-loop traces
- release, package, open PR, open issue, and ops-staleness snapshots
- `artifact_manifest.txt`

## Validation

- Focused SDK/CLI/metadata tests: `50 passed in 1.18s`.
- `python scripts/sdk_release_guard.py --check-mcp-npm`: passed.
- `git diff --check`: passed.
- Artifact hygiene: no local absolute paths or NUL markers found; JSON/JSONL parse passed.

## Repo health

- PR #506 remains the consolidated rolling proof PR.
- PR #508 still has failing/cancelled Python CI for the setup-go Dependabot bump guardrail expectation.
- PRs #509 and #510 are green but require human review.
- Issue #473 still tracks stale ops docs; roadmap is 2 weeks old and architecture is 3 weeks old.
- Release/package alignment remains GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`.
- Distribution drift remains: MCP Registry metadata is stale at `0.2.1`; Glama tool indexing remains a follow-up.

## Recommended next task

Review and merge the green Dependabot PRs #509 and #510, then continue using
#506/#490 as the single rolling dogfood proof sink until the proof PR receives
human review.
