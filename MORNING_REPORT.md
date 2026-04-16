# Morning Report

## Mission
Audit the repo's Claude-specific instruction surface so Claude Code works with the harness it already has instead of carrying a stale, oversized repo prompt.

## What shipped
- added `CLAUDE_MD_AUDIT.md` with source-backed findings and follow-up guidance
- trimmed `CLAUDE.md` down to the AgentGuard-specific repo contract
- removed stale embedded architecture/API detail from `CLAUDE.md` and pointed it at `ARCHITECTURE.md`
- kept `AGENTS.md` unchanged because the actual issue was Claude-specific duplication, not a repo-wide policy error

## Why it matters
- Claude Code already injects tool, style, memory, skill, and environment guidance
- the old `CLAUDE.md` was wasting context and had started drifting from the real repo
- the new file is shorter, more durable, and sharper about SDK boundaries, proof expectations, and distribution priorities

## Validation
- source article reviewed directly
- `python scripts/sdk_preflight.py` passed
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80` passed: `672 passed`, `92.97%` coverage
- `python scripts/sdk_release_guard.py` passed
- `CLAUDE.md` reduced from `1568` words / `11890` characters to `525` words / `3613` characters
- proof artifacts saved under `proof/claude-md-audit/`
- local full-repo `ruff` still reports unrelated pre-existing issues in untouched SDK tests; saved in `proof/claude-md-audit/lint.txt`

## Notes
- I did not edit `AGENTS.md` in this PR because the queue item was specifically about Claude Code system-prompt overlap
- if we later want one shared source for agent instructions across Codex and Claude, that should be a separate deduplication pass rather than hidden in this audit PR
