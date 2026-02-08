# Technical Architecture

## System overview

Two products in one repo:

1. **SDK** (`sdk/`) — Python package `agentguard47`. Zero stdlib-only dependencies, Python 3.9+.
2. **Dashboard** (`dashboard/`) — Next.js 14 App Router SaaS. Direct Postgres, NextAuth, Stripe.

## SDK architecture

### Key modules
| Module | Purpose |
|--------|---------|
| `tracing.py` | Tracer, TraceSink, TraceContext, JsonlFileSink, StdoutSink |
| `guards.py` | LoopGuard, BudgetGuard, TimeoutGuard + exceptions |
| `instrument.py` | @trace_agent, @trace_tool, patch_openai, patch_anthropic |
| `sinks/` | HttpSink (batched background thread) — bridge to dashboard |
| `integrations/` | LangChain BaseCallbackHandler |
| `evaluation.py` | EvalSuite — chainable assertion-based trace analysis |
| `recording.py` | Recorder, Replayer (deterministic replay) |
| `cli.py` | CLI: report, summarize, view, eval |

### Event schema (JSONL)
```json
{
  "service": "my-agent",
  "kind": "span|event",
  "phase": "start|end|emit",
  "trace_id": "<uuid>",
  "span_id": "<uuid>",
  "parent_id": "<uuid|null>",
  "name": "agent.run",
  "ts": 1738690000.123,
  "duration_ms": 42.5,
  "data": {},
  "error": { "type": "LoopDetected", "message": "..." },
  "cost_usd": 0.003
}
```

## Dashboard architecture

### Stack
- Next.js 14 (App Router, server components)
- Postgres via `postgres` npm package (direct connection, not Supabase JS)
- NextAuth 4 (credentials provider, bcryptjs, JWT sessions)
- Stripe (checkout, customer portal, webhooks)
- Zod (request validation)
- Vercel (hosting, cron)

### Data flow
```
SDK HttpSink
  → POST /api/ingest (NDJSON, Bearer ag_xxx)
  → rate limit (100/min per IP)
  → API key hash lookup → team resolution
  → usage quota check against plan
  → Zod schema validation
  → batch INSERT INTO events (unnest)
  → usage counter increment (INSERT...ON CONFLICT)

Read API (GET /api/v1/*)
  → rate limit (60/min per IP)
  → API key hash lookup → team resolution
  → query functions from queries.ts
  → JSON response

MCP Server (stdio)
  → HTTP client calls Read API
  → returns structured tool results to AI agent
```

### Database schema

```sql
-- Core tables
teams (id, owner_id, name, plan, created_at)
users (id, email, password_hash, created_at)
api_keys (id, team_id, name, prefix, key_hash, revoked_at, created_at)
events (id, team_id, trace_id, span_id, parent_id, kind, phase, name,
        ts, duration_ms, data, error, service, api_key_id, cost_usd, created_at)
usage (team_id, month, event_count)  -- PK: (team_id, month)

-- Billing
customers (id, team_id, stripe_customer_id, created_at)

-- Sharing
shared_traces (id, team_id, trace_id, slug, created_at, expires_at)
```

### Key files
- `src/lib/db.ts` — Lazy-init Postgres, proxy wrapper for tagged templates
- `src/lib/api-auth.ts` — Reusable Bearer token auth for read API
- `src/lib/queries.ts` — SQL query functions (traces, usage, costs, alerts)
- `src/lib/plans.ts` — Plan definitions (free/pro/team limits)
- `src/app/api/ingest/route.ts` — Critical ingest endpoint
- `src/app/api/v1/` — Versioned read API endpoints

## MCP server architecture

### Package: `@agentguard47/mcp-server`

Standalone Node.js process using `@modelcontextprotocol/sdk`. Communicates via stdio transport.

- `src/client.ts` — HTTP client wrapping `/api/v1/` endpoints
- `src/tools.ts` — 6 MCP tool definitions
- `src/index.ts` — Server entry point, tool registration

### Configuration
- `AGENTGUARD_API_KEY` (required) — Bearer token for read API
- `AGENTGUARD_URL` (optional) — defaults to production

## Extensibility
- Add sinks (S3, OTLP, HTTP — HttpSink already ships)
- Add framework adapters (LangChain ships, CrewAI/AutoGen planned)
- Add MCP tools as new read API endpoints are added
