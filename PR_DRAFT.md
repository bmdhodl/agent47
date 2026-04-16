# PR Draft

## Title
Audit and slim `CLAUDE.md` to match Claude Code's actual system prompt behavior

## Summary
- add `CLAUDE_MD_AUDIT.md` documenting what Claude Code already injects and what should stay repo-local
- trim `CLAUDE.md` from a long mixed prompt into a focused AgentGuard repo contract
- keep Claude guidance aligned with `memory/`, `ops/`, and `ARCHITECTURE.md` instead of embedding stale architecture and API detail

## Scope
- `CLAUDE.md`
- `CLAUDE_MD_AUDIT.md`
- `PR_DRAFT.md`
- `MORNING_REPORT.md`
- proof artifacts under `proof/claude-md-audit/`

## Non-goals
- no SDK runtime changes
- no dashboard work
- no Codex-specific prompt rewrite in `AGENTS.md`
- no attempt to document all Claude Code internals in-repo

## Proof
- source article reviewed: https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html
- `python scripts/sdk_preflight.py`
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- token-count proof saved in `proof/claude-md-audit/token-counts.txt`
- local audit evidence saved in `proof/claude-md-audit/`
- full PR CI and CodeQL must pass before merge

## Saved artifacts
- `proof/claude-md-audit/check.txt`
- `proof/claude-md-audit/preflight.txt`
- `proof/claude-md-audit/release-guard.txt`
- `proof/claude-md-audit/token-counts.txt`
- `proof/claude-md-audit/lint.txt`
- `proof/claude-md-audit/security.txt`
