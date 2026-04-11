# CLAUDE.md

Claude Code already injects broad tool, style, memory, and session guidance.
This file is only for AgentGuard-specific repo rules that Claude would not know
otherwise.

## Read First

Before touching code or docs, read these files in this order:

1. `memory/state.md`
2. `memory/blockers.md`
3. `memory/decisions.md`
4. `memory/distribution.md`
5. `ops/00-NORTHSTAR.md`
6. `ops/03-ROADMAP_NOW_NEXT_LATER.md`
7. `ops/04-DEFINITION_OF_DONE.md`
8. `ARCHITECTURE.md`

If `memory/` conflicts with older repo docs, `memory/` wins.

## Repo Boundary

AgentGuard is the public SDK wedge.

- `sdk/` = zero-dependency Python runtime guardrails SDK
- `mcp-server/` = narrow read-only MCP surface
- hosted dashboard = private repo, out of scope here

Non-negotiable:

- SDK stays free, MIT, and zero-dependency
- distribution beats random feature expansion
- focus stays on runtime enforcement + coding-agent safety
- do not add paid/dashboard features in this repo
- do not put business-sensitive plans or outreach data in this repo

## Claude Repo Contract

Before coding, explicitly restate:

- goal
- scope
- non-goals
- done criteria tied to `ops/04-DEFINITION_OF_DONE.md`

If `ops/03-ROADMAP_NOW_NEXT_LATER.md` is older than 5 days or
`ops/02-ARCHITECTURE.md` is older than 14 days, warn before starting work.

Always:

- read before editing
- keep changes minimal and product-facing
- stop if the request conflicts with `memory/` or `ops/`
- leave proof for every PR
- do the post-PR review loop: CI, automated review, comment sweep, fixes, rerun

## What Claude Should Optimize For Here

- onboarding and activation
- docs, quickstarts, and starter quality
- SDK hardening and tests
- eval/report/incident proof surfaces
- release-readiness and metadata consistency
- distribution-supporting assets tied to the actual SDK and MCP product

Avoid:

- dashboard-only work
- speculative framework sprawl
- broad observability positioning
- novelty features with weak adoption value
- large refactors without user-facing payoff

## Repo-Specific Workflow

Prefer the repo commands:

```bash
make preflight
make check
make structural
make security
make release-guard
```

If `make` is unavailable, run the direct equivalents and save the output as
proof.

Use the repo's existing proof discipline:

- save artifacts under `proof/<task-name>/`
- update `PR_DRAFT.md`
- update `MORNING_REPORT.md`

After a merged PR, add one short SDK-only entry to `inbox/log.md`.

## Architecture Notes That Matter For Claude

- Public API stability flows through `sdk/agentguard/__init__.py`
- core SDK modules stay stdlib-only
- one-way import direction matters; do not create core-module cycles
- guards raise exceptions rather than returning booleans
- local-first proof matters: `doctor`, `demo`, `quickstart`, starter files,
  JSONL traces, `report`, `incident`, `decisions`

Read `ARCHITECTURE.md` for the current directory map and data flow instead of
copying stale module graphs into new docs.

## Claude-Specific Opportunities

Use Claude Code features that already exist instead of re-describing them here:

- built-in memory features where available, plus repo `memory/`
- surfaced skills and tool guidance from Claude Code itself
- repo-local Claude assets under `.claude/agents/` when they help

For this repo, the most relevant Claude-side assets are:

- `.claude/agents/sdk-dev.md`
- `.claude/agents/pm.md`
- `memory/`
- `ARCHITECTURE.md`

## Current Product Snapshot

- package: `agentguard47`
- official MCP Registry listing: live
- dashboard remains private

Current: latest shipped release: v1.2.7.
Current: latest shipped release is 1.2.7.

Core message to preserve:

AgentGuard stops coding agents from looping, retrying forever, and burning
budget.
