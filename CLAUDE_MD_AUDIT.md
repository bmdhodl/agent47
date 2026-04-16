# CLAUDE.md Audit

Date: 2026-04-11

Primary source reviewed:
- [How Claude Code Builds a System Prompt](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html)

Repo files reviewed:
- `CLAUDE.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.claude/agents/sdk-dev.md`
- `.claude/agents/pm.md`

## Summary

The old `CLAUDE.md` was doing too much. It repeated broad Claude Code harness behavior that the product already injects, and it had started to drift from the actual repo architecture and SDK surface. The fix was to turn `CLAUDE.md` into a slim repo-specific contract and move the detailed analysis into this audit file.

`AGENTS.md` was reviewed for repo drift, but not changed in this PR because the queue task is Claude-specific and the current issues were mostly duplication against Claude Code's own system prompt rather than Codex behavior.

## Source Takeaways

From the source article, Claude Code already injects conditional guidance for:

- general tool usage and preference for dedicated tools
- tone and output efficiency
- risky-action confirmation
- memory behavior
- skill invocation and skill discovery
- environment and worktree context
- MCP per-server instructions

That means repo `CLAUDE.md` files should bias toward:

- repo-specific rules
- product boundaries
- local workflow requirements
- proof requirements
- references to current architecture and memory files

They should avoid re-explaining generic Claude harness behavior unless the repo truly needs to override it.

## Findings

| Area | Finding | Severity | Action |
|------|---------|----------|--------|
| Token waste | The old `CLAUDE.md` repeated many generic harness behaviors Claude Code already injects: tool guidance, communication structure, prompt style, shell workflow, and general task philosophy. | High | Trimmed the file to repo-specific instructions only. |
| Drift risk | The old `CLAUDE.md` embedded a large module graph and API snapshot that had already drifted from the current repo. It missed newer modules and surfaces such as `decision.py`, `skillpack.py`, `doctor.py`, `repo_config.py`, `profiles.py`, and newer guards. | High | Replaced stale embedded architecture detail with a pointer to `ARCHITECTURE.md` as the current source of truth. |
| Claude feature usage | The old `CLAUDE.md` did not clearly acknowledge that Claude Code already has memory and skill discovery machinery. That makes repo instructions more likely to fight the harness or waste context. | Medium | Added a short Claude-specific section telling the model to use built-in memory/skills plus repo `memory/` and `.claude/agents/`. |
| Repo boundary clarity | The old file mixed repo identity, workflow, architecture, navigation guide, and AI-facing API details into one long prompt document. Important SDK boundary rules were there, but buried. | Medium | Promoted repo boundary and non-negotiables to the top-level contract. |
| AGENTS.md overlap | `AGENTS.md` overlaps with `CLAUDE.md` in some repo rules, but that is acceptable because `AGENTS.md` is not Claude-specific and serves a different agent runtime. | Low | No change in this PR. Consider future shared-source generation only if cross-agent drift becomes active pain. |

## Changes Made

### `CLAUDE.md`

Kept:

- required `memory/` and `ops/` read order
- SDK boundary and non-negotiables
- before-coding restatement requirement
- proof and PR review-loop requirement
- repo-specific workflow commands
- inbox update rule
- architecture constraints that materially affect Claude work here
- current product snapshot and core positioning

Removed or compressed:

- broad tool/style/session instructions that Claude Code already injects
- large embedded architecture graph
- detailed agent navigation guides already covered better elsewhere
- stale public API inventory
- duplicated command sections that did not change Claude behavior in this repo

### `AGENTS.md`

No changes in this PR.

Reason:
- the audit target was Claude Code behavior
- the major issue was duplication against Claude's built-in prompt assembly, not a repo-wide policy error
- `AGENTS.md` can be reviewed separately if we decide to deduplicate cross-agent docs later

## Before / After Size

Count method:
- PowerShell `Get-Content CLAUDE.md | Measure-Object -Word -Character`

`CLAUDE.md` before:
- words: `1568`
- characters: `11890`

`CLAUDE.md` after:
- words: `525`
- characters: `3613`

Delta:
- words: `-1043`
- characters: `-8277`

## Why This Is Better

- less prompt waste in Claude Code sessions
- less risk of fighting Claude's built-in conditional sections
- less architecture drift because `CLAUDE.md` now points to `ARCHITECTURE.md`
- sharper repo contract: SDK boundary, local proof, and distribution priorities are easier to find

## Follow-Up Considerations

Not for this PR, but worth considering later:

1. If `AGENTS.md`, `CLAUDE.md`, and future agent instruction files keep drifting, generate shared repo policy blocks from one source file and inject agent-specific deltas on top.
2. Keep `ARCHITECTURE.md` current so Claude-facing docs can stay slim without losing accuracy.
3. If Claude Code exposes more stable skill-discovery affordances, consider documenting how `agentguard skillpack` should interact with them in a separate guide rather than in `CLAUDE.md`.
