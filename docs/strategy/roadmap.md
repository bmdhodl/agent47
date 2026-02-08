# Roadmap

Forward-looking priorities. See `execution_plan.md` for completed phases.

## Now: Ship and validate

### MCP server to npm
- Publish `@agentguard47/mcp-server` to npm under `@agentguard47` scope
- Write setup guide for Claude Code, Cursor, Windsurf
- Measure installs and tool call volume

### Public trace sharing polish
- Run `shared_traces` migration on production DB
- Test share flow end-to-end (create, view, expire, delete)
- Add shared trace count to usage/analytics

### First paying customers
- Drive free tier signups via SDK README and content
- Monitor upgrade triggers (quota exceeded, retention limit)
- Collect feedback from first Pro/Team upgrades

## Next: Team features

### Team invites
- `team_members` table with role column
- Invite API (email-based) + accept flow
- Settings UI for team management
- Fulfills Team plan's "10 users" promise

### Real-time alerts
- Alert rules (budget threshold, error rate, loop frequency)
- Email notifications (Resend integration)
- Slack webhook integration
- Alert history in dashboard

## Later: Ecosystem expansion

### More framework integrations
- CrewAI adapter
- AutoGen adapter
- LlamaIndex adapter
- Each integration = new community distribution channel

### Community eval templates
- Preset EvalSuite configs: no_runaway.py, budget_check.py, latency_sla.py
- Users import and reuse → faster time-to-value

### Write-capable MCP tools
- Share trace from MCP (agent creates share links)
- Create alert rules from MCP
- Agent-to-agent trace sharing

### Scale infrastructure
- Multi-region ingest (edge functions)
- Trace search with full-text and structured filters
- Custom dashboards and saved views
- SOC 2 compliance
- Enterprise SSO (SAML/OIDC)

## Non-goals (for now)
- No-code agent builders
- Full workflow runtime
- Vertical-specific automation
- Self-hosted dashboard (SaaS only)
