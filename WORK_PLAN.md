# WORK_PLAN — Ship AgentGuard as Claude Code skill

## Problem
VoltAgent's awesome-agent-skills indexes packaged Claude Code / Codex / Cursor / Gemini skills. AgentGuard fits the safety/cost-control niche but has no entry. agent47 has a root `SKILL.md` (Anthropic format) but no namespaced `skills/agentguard/` Claude Code package and no Codex-format mirror.

## Approach
1. Add `skills/agentguard/SKILL.md` — Claude Code skill format with name + description frontmatter and trigger conditions in body. Mirror content tightly to root `SKILL.md` so they don't drift.
2. Add `skills/codex/agentguard.md` — Codex skill format mirror (single file).
3. Add `skills/README.md` orienting readers to which format to use.
4. Defer the awesome-agent-skills PR. Their CONTRIBUTING.md explicitly requires "real community usage and proven adoption (not brand-new submissions)." Submitting a brand-new skill file the same hour the directory is created violates their gate. Instead, ship the skill files in agent47 first, let them mature ~2 weeks, then queue a follow-up awesome PR with usage evidence. Decision logged in PR body + new Queue task.
5. Open small separate PR to bmdpat adding "Install via Claude Code skill" snippet to AgentGuard tools page.

## Files to touch
- `skills/agentguard/SKILL.md` (new)
- `skills/codex/agentguard.md` (new)
- `skills/README.md` (new)
- (bmdpat) tools/agentguard page — separate PR

## Done criteria
- [ ] `skills/agentguard/SKILL.md` exists, valid frontmatter, points to `agentguard47` PyPI
- [ ] `skills/codex/agentguard.md` mirrors content
- [ ] `skills/README.md` explains both formats
- [ ] PR open on agent47 with green checks
- [ ] bmdpat tools page mentions skill install (separate PR)
- [ ] awesome-agent-skills PR deferred — new Queue/agent47 task created for ~2 weeks out

## Risks
- Drift between root `SKILL.md` and `skills/agentguard/SKILL.md` — mitigation: `skills/` version stays terse and links to root for full reference.
- Awesome list gate may reject even a mature submission — acceptable; deferring respects their stated rule.
