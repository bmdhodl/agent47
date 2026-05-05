# RESEARCH — AgentGuard skill packaging

## Existing SKILL.md (verified)
`K:\agent47\SKILL.md` already exists with Anthropic Claude Skills frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`). PyPI package: `agentguard47`. Import: `from agentguard import ...`. CLI: `agentguard doctor|demo|report|eval|incident`. 4-line quick-start uses `BudgetGuard`, `Tracer`, `patch_openai`.

## Skill format research
- **Claude Code / Anthropic skills** — `SKILL.md` with YAML frontmatter (`name`, `description`; optional `license`, `compatibility`, `metadata`). Body is markdown with install + trigger conditions + examples. Multiple skills per repo go in `skills/<skill-name>/SKILL.md`.
- **Codex skills** — single markdown file under `skills/codex/<name>.md` (or `.codex/skills/`). Frontmatter optional but `name`/`description` recommended.

## awesome-agent-skills (VoltAgent) submission rules
Verified via raw CONTRIBUTING.md fetch:
- Format: `- **[author/skill-name](url)** - description (<=10 words)`
- Add to end of an EXISTING category. No "Safety / Cost Control" section exists. Closest fits: Community Skills > AI and Data, or Other.
- Quality gate: "real community usage and proven adoption (not brand-new submissions)" — explicit blocker for same-day submissions.
- PR title format: `Add skill: bmdhodl/agentguard`
- Public repo + working skill + README/SKILL.md + author prefix all required.

## Decision: defer awesome-agent-skills PR
Submitting a same-day-created skill violates their stated adoption gate. Right path:
1. Ship skill files in agent47 now (this PR).
2. Let them be referenced/installed ~2 weeks.
3. Queue follow-up task for awesome PR with download/issue evidence.

Decision logged in PR body + new Queue/agent47 task created for the follow-up.

## Repo state at start
- PR #442 merged on origin/main as squash `0d39f02`. Local was on pre-squash `feat/deployed-agent-preset`. Step 0 cut new branch `feat/agentguard-claude-code-skill` from `origin/main`.
- Worktree at `C:/Users/patri/.codex/worktrees/agent47-release-hygiene` holds `main` — could not check out main locally; cut feat branch from `origin/main` directly.
- Stragglers from PR #442 found at repo root: `WORK_PLAN.md`, `RESEARCH.md`, `QA_REPORT.md`, `PR_DRAFT.md`, `MORNING_REPORT.md`, `FOLLOWUP.md`, `CLAUDE_MD_AUDIT.md`. Treated as throwaway worker scratch and overwritten for this run.
