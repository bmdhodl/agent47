# Product Requirements

## Target user
Solo developers and small teams building multi-agent workflows who need to debug, monitor, and guard agent behavior.

## Primary jobs-to-be-done
- Understand why an agent made a specific decision
- Prevent costly loops and runaway tool usage
- Reproduce a run deterministically for tests
- Monitor agent costs, usage, and alerts in a hosted dashboard
- Let AI agents inspect their own traces and budgets programmatically

## Shipped features

### SDK (agentguard47 on PyPI)
1. Trace capture — JSONL locally, HttpSink to hosted dashboard
2. Loop, budget, and timeout guards with clear exceptions
3. Deterministic record/replay
4. LangChain integration (BaseCallbackHandler)
5. EvalSuite for assertion-based trace analysis
6. CLI: report, summarize, view, eval
7. Patch helpers for OpenAI and Anthropic clients

### Hosted dashboard (Next.js SaaS)
1. Auth (NextAuth credentials + JWT)
2. Trace list and Gantt visualization
3. Cost tracking (by model, by API key, expensive traces)
4. Usage monitoring with plan-based quotas
5. Alert view (guard triggers + errors)
6. API key management (ag_ prefix, SHA-256 hashed)
7. Billing (Stripe checkout, portal, webhooks)
8. Data retention enforcement (daily cron)

### Read API (v1)
1. GET /api/v1/traces — list with filters (service, time range, pagination)
2. GET /api/v1/traces/:id — full event tree
3. GET /api/v1/alerts — guard alerts and errors
4. GET /api/v1/usage — quota and plan limits
5. GET /api/v1/costs — monthly spend, by-model breakdown, savings

### MCP Server (@agentguard47/mcp-server)
1. query_traces, get_trace, get_alerts, get_usage, get_costs, check_budget
2. Connects AI coding agents (Claude Code, Cursor) to the read API

### Public trace sharing
1. Shareable trace links with optional expiry
2. Public Gantt view with OG meta tags
3. "Powered by AgentGuard" CTA

## Out of scope (current)
- Fine-grained permission model (team roles)
- Real-time alerting (email/Slack/PagerDuty)
- Multi-tenant team member management

## Success metrics
- Time-to-first-trace < 5 minutes
- MRR from Pro/Team plans
- Active teams sending traces per week
- MCP server installs (npm weekly downloads)
- Shared trace links created per month
