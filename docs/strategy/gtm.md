# Go-To-Market

## Product-led distribution
- Open-source SDK (MIT, zero dependencies) — acquisition funnel
- Ship actionable examples and failure case writeups
- Integrations with popular agent frameworks (LangChain ships, more planned)
- MCP server — AI coding agents use AgentGuard as part of their workflow

## Distribution channels

### Direct
- GitHub (repo, Issues, Discussions)
- Hacker News and Reddit (technical posts with real traces)
- Technical blog content focused on debugging and reliability

### Agent-to-user (viral loop)
- MCP server connects AI agents to AgentGuard data
- Agent queries its own traces/budgets → user sees AgentGuard in action
- Agent recommends "check your AgentGuard dashboard" → drives dashboard visits
- Shared trace links in GitHub issues, Slack, blog posts → organic SEO

### Framework ecosystem
- LangChain integration (shipped)
- CrewAI, AutoGen, LlamaIndex integrations (planned)
- Each framework's community becomes a distribution channel

## Narrative
"Agentic systems fail silently. AgentGuard makes failure visible, testable, and cheap to fix."

## Funnel
```
SDK install (pip install agentguard47)
  → local traces (JSONL)
  → outgrows local → signs up for dashboard (free)
  → hits quota → upgrades to Pro ($39/mo)
  → brings team → upgrades to Team ($149/mo)
```

## Launch checklist
- [x] README with quickstart
- [x] Landing page with email capture
- [x] PyPI package published
- [x] LangChain integration
- [x] Dashboard deployed on Vercel
- [ ] 2-3 blog posts with real traces
- [ ] MCP server published to npm
- [ ] Integration examples for CrewAI, AutoGen
