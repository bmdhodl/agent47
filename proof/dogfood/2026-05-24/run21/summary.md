# AgentGuard Dogfood Run 21 - 2026-05-24

## Goal

Keep the public AgentGuard SDK dogfood loop running under AgentGuard and leave durable proof that local guard enforcement still works.

## Scope

- Proof artifacts under `proof/dogfood/2026-05-24/run21/`
- Rolling GitHub proof sinks: PR `#506` and issue `#490`

## Non-goals

- No dashboard, auth, billing, deployment, secret, paid-feature, or release work.
- No new SDK runtime features or dependency changes.

## Done Criteria

Per `ops/04-DEFINITION_OF_DONE.md`, this proof-only run needs concrete command output, targeted runtime evidence, no hardcoded local paths in committed artifacts, and review of docs/roadmap drift. The full `make check` path was not necessary because this run only adds proof artifacts; the focused dogfood/CLI/metadata validation slice passed.

## Staleness Warning

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 2 weeks old
- `ops/02-ARCHITECTURE.md`: 3 weeks old
- Existing tracker: issue `#473`

## Plan

1. Verify repo identity, SDK memory, ops docs, and current package/distribution state.
2. Run installed and repo-local `doctor` / `demo` paths plus the coding-agent review-loop example.
3. Inspect raw JSONL traces and save parsed guard events.
4. Save release, PR, issue, and review-thread snapshots.
5. Run focused validation and update PR `#506` / issue `#490`.

## Commands Run

Key commands are recorded in `commands.txt`. The proof path included:

- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-24/run21/repo-local-demo-traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-24/run21/review-loop-traces.jsonl`

## Guard Behavior Observed

Parsed events are saved in `guard_events.json` and summarized in `trace_inspection.txt`.

- `doctor.verify`: 4 events across installed and repo-local doctor traces.
- `guard.budget_warning`: 2 events from installed and repo-local demo traces.
- `guard.budget_exceeded`: 3 events total.
- `guard.loop_detected`: 2 events from installed and repo-local demo traces.
- `guard.retry_limit_exceeded`: 3 events total.

Concrete enforcement:

- Installed demo stopped a cost overrun: `$1.0800 > $1.0000`.
- Repo-local demo stopped the same cost overrun: `$1.0800 > $1.0000`.
- Installed and repo-local demo detected repeated `tool.search({"query":"python asyncio"})`.
- Installed and repo-local demo stopped `fetch_docs` after 3 attempts with a limit of 2.
- Review-loop proof stopped budget overrun on attempt 3.
- Review-loop proof stopped `apply_patch` after attempt 4 with retry enforcement.

## Validation

- Focused tests: `35 passed in 2.78s` in `pytest-focused.txt`.
- Release guard: `Release guard passed.` in `release_guard.txt`.
- Artifact hygiene: no BOM, no NUL bytes, no local path leaks, and JSON parsed in `artifact_hygiene.txt`.
- Review-thread sweep: 25 open PRs, 0 active unresolved non-outdated review threads in `all_open_pr_review_thread_summary.json`.
- PR `#506` review-thread sweep: 0 active unresolved non-outdated review threads in `review_thread_summary.json`.

## Distribution Snapshot

- GitHub release: `v1.2.10`, published 2026-05-02.
- PyPI latest/installed: `agentguard47==1.2.10`.
- Local SDK version: `1.2.10`.
- npm MCP package: `@agentguard47/mcp-server@0.2.2`.
- Local MCP package/server metadata: `0.2.2`.
- Known external drift remains: MCP Registry public metadata still needs refresh and Glama tool indexing still needs follow-up from `ops/FOLLOWUP.md`.

## Repo Status

- PR `#506` is the rolling dogfood proof PR and remains green but `REVIEW_REQUIRED`.
- PR `#508` still has failing/cancelled Python checks from the setup-go Dependabot bump.
- PRs `#509` and `#510` are green and require human review.
- Issues `#512` through `#515` still look like scanner-noise tech-debt items and need triage before action.
- Issue `#473` continues to track stale roadmap/architecture docs.

## Diff Summary

- Added this run's proof bundle under `proof/dogfood/2026-05-24/run21/`.
- No SDK runtime, docs, dashboard, auth, billing, deployment, or dependency files changed.

## Docs Updates Needed

- No docs update needed for this proof artifact.
- Separate hygiene remains: refresh `ops/03-ROADMAP_NOW_NEXT_LATER.md` and `ops/02-ARCHITECTURE.md` under issue `#473`.
