# Publishing Blog Posts

Step-by-step instructions for cross-posting AgentGuard blog posts to Dev.to, Hashnode, and Medium.

## Dev.to

1. Go to [dev.to/enter](https://dev.to/enter) and sign in
2. Click **Write a Post**
3. Copy the entire markdown file content (including the frontmatter `---` block)
4. Paste into the editor — Dev.to reads the frontmatter automatically:
   - `title` → post title
   - `tags` → post tags (max 4)
   - `description` → meta description
   - `canonical_url` → prevents SEO duplicate penalty
   - `published: true` → publishes immediately (set to `false` for draft)
5. Preview, then publish

**Tags to use:** `ai`, `python`, `opensource`, `devops`, `agents`, `openai`, `cicd`
(Dev.to allows max 4 tags per post — pick the most relevant)

## Hashnode

1. Go to [hashnode.com](https://hashnode.com) and sign in
2. Click **Write an article**
3. Paste markdown content (without frontmatter)
4. Set manually:
   - **Title** — from the `title` field in frontmatter
   - **Tags** — from the `tags` field
   - **Canonical URL** — from the `canonical_url` field (under SEO settings)
5. Publish

## Medium

1. Go to [medium.com/new-story](https://medium.com/new-story)
2. Paste markdown — Medium will auto-format (code blocks may need manual cleanup)
3. Add tags (Medium allows up to 5): `AI`, `Python`, `DevOps`, `Open Source`, `Machine Learning`
4. Set canonical URL: Settings → This story was originally published on → paste the `canonical_url`
5. Publish

## Post Checklist

Before publishing each post:

- [ ] All code examples run against `agentguard47==1.2.1`
- [ ] `canonical_url` points to the GitHub source file
- [ ] Links to repo (`github.com/bmdhodl/agent47`) are correct
- [ ] `pip install agentguard47` command is correct
- [ ] No broken images or links
- [ ] Preview looks clean on the target platform

## Posts Ready to Publish

| File | Title | Platforms |
|------|-------|-----------|
| `001-why-agents-loop-devto.md` | Why Your AI Agent Loops (And How to See It) | Dev.to, Hashnode |
| `002-budget-enforcement-patterns-devto.md` | 3 Patterns for Enforcing AI Agent Budgets in Python | Dev.to, Hashnode |
| `003-ci-cost-gates-devto.md` | How to Add Cost Gates to Your AI Agent CI Pipeline | Dev.to, Hashnode |
