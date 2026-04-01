# Community Engagement Plan

Goal: establish AgentGuard as the runtime-guardrails tool for coding-agent
safety by showing up where agent builders already talk about loops, retries,
runaway spend, and broken automation.

## Priority Channels

| Channel | Why it matters | Frequency |
|---------|----------------|-----------|
| LangChain Forum / GitHub Discussions | Agent builders already report loop and cost pain there | 2x/week |
| LangGraph issues / discussions | Strong overlap with graph-style agent failures | 2x/week |
| CrewAI discussions | Cost and retry pain shows up in agent workflow threads | 1x/week |
| Hacker News comments | High-leverage technical feedback after launch | launch day + follow-ups |
| LinkedIn | Proof-of-work clips for engineers and engineering leaders | 1x/week |

## What to look for

### 1. "My agent is stuck in a loop"
- Response angle: `LoopGuard` and `FuzzyLoopGuard`

### 2. "This agent keeps retrying"
- Response angle: `RetryGuard`

### 3. "How do I cap agent spend?"
- Response angle: `BudgetGuard`

### 4. "How do I verify an agent safely before production?"
- Response angle: `doctor`, `demo`, `quickstart`, `demo_budget_kill.py`

### 5. "How do I inspect a production incident later?"
- Response angle: local incident report first, optional hosted dashboard later

## Response Rules

1. Be helpful first.
2. Keep replies short and technical.
3. Lead with coding-agent safety, not generic observability.
4. Do not argue about competitors.
5. Disclose that you maintain AgentGuard if asked.
6. Link to the smallest relevant proof, not the whole repo.

## Canonical Assets to Share

- Repo: `https://github.com/bmdhodl/agent47`
- PyPI: `https://pypi.org/project/agentguard47/`
- MCP package: `npx -y @agentguard47/mcp-server`
- Quick local proof:
  - `agentguard doctor`
  - `agentguard demo`
  - `python examples/demo_budget_kill.py`
- Coding-agent onboarding guide:
  - `docs/guides/coding-agents.md`
  - `docs/guides/coding-agent-safety-pack.md`

## Weekly Tracker

| Week | Date | Channel | Thread | Response | Result |
|------|------|---------|--------|----------|--------|
| 1 | | | | | |
| 1 | | | | | |
| 1 | | | | | |

## Metrics

- GitHub stars gained
- PyPI downloads delta
- MCP listing approvals
- Inbound issues/discussions mentioning coding-agent safety
- Organic mentions by other developers
