# RESEARCH — AgentGuard skill packaging

## Existing SKILL.md (verified)
`SKILL.md` at the repo root already exists with Anthropic Claude Skills frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`). PyPI package: `agentguard47`. Import: `from agentguard import ...`. CLI: `agentguard doctor|demo|report|eval|incident`. 4-line quick-start uses `BudgetGuard`, `Tracer`, `patch_openai`.

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
- PR #442 had already merged to `origin/main`, so this task branched from current `origin/main`.
- Repo-root planning artifacts from earlier runs existed at start and were refreshed for this doc-only task.
