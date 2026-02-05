# Launch Post Drafts

## LinkedIn / X (short)
Built a tiny observability SDK for AI agents.

It traces reasoning steps, catches tool loops, and replays runs deterministically.
Zero dependencies. Self-hosted. MIT-licensed.

```
pip install agentguard
```

3 lines of code to trace your agent. 1 guard to catch loops before they burn your budget.

Blog post: "Why Your AI Agent Loops (And How to See It)" [link to blog]

Repo: https://github.com/bmdhodl/agent47

## Hacker News
Title: "Show HN: AgentGuard -- Lightweight observability for multi-agent AI systems"

Body:
I built a zero-dependency Python SDK that traces agent reasoning, detects tool loops, and replays runs deterministically.

The problem: multi-agent systems fail silently. Your agent calls the same tool 10 times in a row, burns $5 in API calls, and returns garbage. Normal observability tools show latency, not reasoning.

AgentGuard gives you:
- Hierarchical tracing with span/event correlation
- Loop detection (catches repeated tool calls automatically)
- Budget and timeout guards
- Deterministic replay for regression tests
- CLI + browser-based trace viewer
- LangChain integration

```
pip install agentguard
```

I wrote up the common failure mode: [Why Your AI Agent Loops](link to blog)

Looking for early users building with LangChain, CrewAI, or custom agent frameworks.

Repo: https://github.com/bmdhodl/agent47
