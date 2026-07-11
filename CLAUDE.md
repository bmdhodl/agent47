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
`ARCHITECTURE.md` is older than 14 days, warn before starting work.

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
- keep PR summaries in the pull request body
- keep active repo follow-ups in `ops/FOLLOWUP.md`
- do not add one-off reports, work plans, or handoff notes to the repo root;
  archive any retained historical notes under `docs/archive/root-reports/`

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

Current release candidate: v1.2.13.
<!-- release candidate is 1.2.13 -->

Core message to preserve:

AgentGuard stops coding agents from looping, retrying forever, and burning
budget.


## Outcome Verification (showwork)

Every agent session that changes this repo records falsifiable claims and closes through the showwork exit gate (github.com/bmdhodl/showwork). Receipts live in `.showwork/` and ship with the PR.

1. Start material work: `python -m showwork.cli start --session <task-slug> --agent <claude-code|codex|gemini>`
2. After each completed change, record a claim with a check that can fail (types: `file_exists`, `file_contains`, `path_moved`, `frontmatter`, `glob_count`, `command`):
   `python -m showwork.cli claim --session <task-slug> --claim "<what changed>" --type file_contains --path <file> --pattern "<regex>"`
3. Before reporting success: `python -m showwork.cli finish --session <task-slug> --status ok`
   - REFUSED (exit 2) means a claimed "done" is not backed by reality. Fix the gap or retract the claim truthfully (`retract`), then finish again. NEVER pass `--no-verify` to manufacture a clean close; if genuinely stuck, `finish --status blocked`.
4. `git add .showwork/` and commit the ledger with your change - the receipt is part of the PR. Do not gitignore it. The ledger is append-only; never rewrite history in it.
5. The Stop hook in `.claude/settings.json` records a claims verdict when a session stops. It observes; it never blocks. The explicit `finish` is the gate.
