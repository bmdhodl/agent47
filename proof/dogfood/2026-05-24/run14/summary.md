# AgentGuard Dogfood Proof - 2026-05-24 run14

## Goal

Keep one real SDK dogfood workflow running under AgentGuard and leave a durable repo plus GitHub proof trail.

## Commands run

- Read AGENTS.md, memory/state.md, memory/blockers.md, memory/decisions.md, memory/distribution.md, ops/00-NORTHSTAR.md, ops/03-ROADMAP_NOW_NEXT_LATER.md, ops/04-DEFINITION_OF_DONE.md, and ops/FOLLOWUP.md.
- Checked roadmap and architecture freshness with git log.
- Checked repo identity, current branch, PR #506, issue #490, open PRs, open issues, release/package metadata, MCP Registry, and Glama.
- Repaired the installed proof path with `python -m pip install -e ./sdk` because ambient import initially pointed at an older editable worktree.
- `agentguard doctor`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report repo_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident repo_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident review_loop_traces.jsonl`
- Focused proof/CLI/metadata pytest slice.
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

- `doctor.verify`: 4 span records across installed and repo-local doctor traces.
- `guard.budget_warning`: 2 events. Demo warned at USD 0.8400 / USD 1.0000.
- `guard.budget_exceeded`: 3 events. Demo stopped at USD 1.0800 > USD 1.0000; review loop stopped at USD 0.0510 > USD 0.0450.
- `guard.loop_detected`: 2 events for repeated `tool.search` calls.
- `guard.retry_limit_exceeded`: 3 events. Demo stopped `fetch_docs` attempt 3 with limit 2; review loop stopped `apply_patch` attempt 4 with limit 3.

## Enforcement verdict

Real enforcement observed. This run counts because the trace files, report, and incident output include concrete guard events, not just successful command exits.

## Package and distribution snapshot

- GitHub release: v1.2.10.
- Local SDK version: 1.2.10.
- PyPI latest: 1.2.10.
- npm MCP package: 0.2.2.
- Local MCP metadata: 0.2.2.
- Official MCP Registry search still reports 0.2.1.
- Glama API still returns an empty tools array.

## Repo health snapshot

- Open PRs: 25.
- Open issues: 15.
- Review-thread sweep: 56 review threads across 25 open PRs, 0 active unresolved non-outdated threads.
- PR #506 refreshed CI and CodeQL are green on final pushed commit f4deba1.
- Post-wait review-thread sweep: 56 review threads across 25 open PRs, 0 active unresolved non-outdated threads.
- PR #506 remains REVIEW_REQUIRED / BLOCKED only on human review.
- PR #508 still has failing/cancelled Python checks from the setup-go Dependabot bump guardrail expectation.
- PRs #509 and #510 remain green but require human review.
- Roadmap is 2 weeks old and architecture is 3 weeks old; issue #473 already tracks docs freshness.

## Validation

- Focused proof/CLI/metadata tests: 35 passed.
- Release guard with MCP npm check: passed.
- Artifact hygiene scan: passed.
- `git diff --check`: passed.

## Files to inspect

- installed_doctor_trace.jsonl
- installed_demo_traces.jsonl
- repo_doctor_trace.jsonl
- repo_demo_traces.jsonl
- review_loop_traces.jsonl
- guard_events.json
- trace_inspection.txt
- repo_demo_report.txt
- repo_demo_incident.md
- review_loop_incident.md
- review_thread_summary.json
