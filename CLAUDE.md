# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AgentGuard — a lightweight observability and runtime-guards SDK for multi-agent AI systems. The SDK is open source (MIT, zero dependencies); the hosted dashboard is the commercial SaaS layer.

- **Repo:** github.com/bmdhodl/agent47
- **Package:** `agentguard47` on PyPI (v0.5.0)
- **Landing page:** site/index.html (Vercel)

## Commands

### SDK (Python)

```bash
# Run all tests (from repo root)
PYTHONPATH=sdk python3 -m unittest discover -s sdk/tests -v

# Run a single test file
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards -v

# Run a single test case
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards.TestLoopGuard.test_loop_detected -v

# Lint
ruff check sdk/agentguard/

# Install SDK in editable mode
pip install -e ./sdk
```

### Dashboard (Next.js)

```bash
cd dashboard
npm ci                # Install deps
npm run dev           # Dev server on localhost:3000
npm run build         # Production build
npm run lint          # ESLint (next lint)
```

### MCP Server

```bash
cd mcp-server
npm ci                # Install deps
npm run build         # Compile TypeScript
npm start             # Run (requires AGENTGUARD_API_KEY env var)
```

### Publishing

```bash
# Bump version in sdk/pyproject.toml, then:
git tag v0.X.0 && git push origin v0.X.0
# publish.yml auto-publishes to PyPI via PYPI_TOKEN
```

## Architecture

**Three products in one repo:**

1. **sdk/** — Python SDK (`agentguard47`). Zero stdlib-only dependencies, Python 3.9+. All tests use `unittest` (no pytest). Public API exports from `agentguard/__init__.py`.

2. **dashboard/** — Next.js 14 App Router + direct Postgres (`postgres` lib, not Supabase JS) + NextAuth (credentials provider, JWT) + Stripe. Deployed to Vercel.

3. **mcp-server/** — MCP server (`@agentguard47/mcp-server`). TypeScript, `@modelcontextprotocol/sdk`. Connects AI agents to the read API via stdio transport.

### SDK Key Modules

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

### Dashboard Data Flow

```
Ingest (write):
  SDK HttpSink → POST /api/ingest (NDJSON, Bearer ag_xxx)
    → rate limit (100/min per IP)
    → API key hash lookup → team resolution
    → usage quota check against plan
    → Zod schema validation
    → batch INSERT INTO events (unnest)
    → usage counter increment (INSERT...ON CONFLICT)

Read API:
  GET /api/v1/* (Bearer ag_xxx)
    → rate limit (60/min per IP)
    → API key auth (api-auth.ts)
    → query functions (queries.ts)
    → JSON response

MCP Server:
  AI Agent → stdio → MCP Server → HTTP → Read API → Postgres
```

### Dashboard Key Files

- `src/lib/db.ts` — Lazy-init Postgres via `DATABASE_URL`, proxy wrapper for tagged template `sql`
- `src/lib/next-auth.ts` — Credentials provider, bcryptjs (12 rounds), rate-limited login
- `src/lib/auth.ts` — `getSessionOrRedirect()`, `getTeamForUser()`
- `src/lib/api-auth.ts` — Reusable Bearer token auth for read API (rate limited 60/min)
- `src/lib/queries.ts` — ~20 SQL query functions (traces, usage, costs, alerts)
- `src/lib/plans.ts` — Plan definitions (free/pro/team limits)
- `src/lib/validation.ts` — Zod schemas for ingest events
- `src/lib/stripe.ts` — Stripe singleton, price mapping
- `src/lib/api-key.ts` — `ag_` prefix key generation, SHA-256 hashed storage
- `src/app/api/ingest/route.ts` — **The critical ingest endpoint**
- `src/app/api/v1/` — **Read API** (traces, alerts, usage, costs) + trace sharing
- `src/app/api/billing/` — Stripe checkout, portal, webhook
- `src/app/api/cron/retention/route.ts` — Daily cleanup (3am UTC via Vercel cron)
- `src/app/share/[slug]/page.tsx` — Public shared trace page (no auth)
- `src/components/share-button.tsx` — Client component for trace sharing
- `src/middleware.ts` — Protects dashboard routes via NextAuth

### Dashboard Path Alias

TypeScript paths: `@/*` maps to `./src/*` (e.g., `import { sql } from "@/lib/db"`)

### Dashboard Route Groups

- `(auth)/` — Login, signup (public)
- `(dashboard)/` — Protected: traces, costs, usage, alerts, settings, security, help
- `share/` — Public shared trace pages (no auth)
- `api/v1/` — Versioned read API (Bearer auth, separate from session auth)

## SDK Conventions

- **Zero dependencies.** Stdlib only. Optional extras: `langchain-core>=0.1`.
- **Trace format:** JSONL — `{service, kind, phase, trace_id, span_id, parent_id, name, ts, duration_ms, data, error, cost_usd}`
- **Guards raise exceptions:** `LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`
- **TraceSink interface:** All sinks implement `emit(event: Dict)`

## Dashboard Environment Variables

```bash
DATABASE_URL=postgresql://...          # Direct Postgres (Supabase-hosted)
NEXTAUTH_SECRET=...                    # JWT signing (openssl rand -base64 32)
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_TEAM=price_...
CRON_SECRET=...                        # Vercel cron auth
```

## Pricing Tiers

- **Free:** 10K events/month, 7-day retention, 2 keys
- **Pro ($39/mo):** 500K events, 30-day retention, 5 keys
- **Team ($149/mo):** 5M events, 90-day retention, 20 keys, 10 users

## CI/CD

- **ci.yml:** Python 3.9-3.12 matrix tests + ruff lint + dashboard lint/build. Runs on push/PR.
- **deploy.yml:** Vercel deploy on push to main (dashboard changes) or PR preview.
- **publish.yml:** PyPI publish on `v*` tags.
- **scout.yml:** Daily cron — finds GitHub issues for outreach, creates tracking Issue.

## Key Decisions

- SDK is the acquisition funnel. Must stay free, MIT, zero-dependency.
- Dashboard is the paywall. Users who outgrow local JSONL files upgrade.
- HttpSink is the bridge — point it at `/api/ingest` and traces flow to dashboard.
- No Supabase JS client. Direct Postgres via connection string. Auth is NextAuth, not Supabase Auth.

## Agent Workflow

This project uses role-based Claude Code agents. Each agent has a prompt file in `.claude/agents/`.

| Role | File | Scope |
|------|------|-------|
| **PM** | `.claude/agents/pm.md` | Triage, prioritize, coordinate, unblock |
| **SDK Dev** | `.claude/agents/sdk-dev.md` | `component:sdk` — Python SDK code + tests |
| **Dashboard Dev** | `.claude/agents/dashboard-dev.md` | `component:dashboard` + `component:api` |
| **Marketing** | `.claude/agents/marketing.md` | Docs, README, launch materials, outreach |

**To start an agent session:** Open Claude Code in this repo and say:
```
Read .claude/agents/sdk-dev.md and follow those instructions.
```

**Project board:** https://github.com/users/bmdhodl/projects/4

**How agents coordinate:**
- The GitHub project board is the single source of truth.
- Issues are separated by `component:` labels (sdk, dashboard, api, infra).
- Agents pick up Todo items, move to In Progress, do the work, close when done.
- Cross-agent dependencies are handled via issue comments and references.
- When blocked, agents comment on the issue and tag the blocking issue number.
- New work discovered during implementation gets filed as new issues with proper labels.

**Phase progression:** v0.5.1 → v0.6.0 → v0.7.0 → v0.8.0 → v0.9.0 → v1.0.0

## What NOT To Do

- Do not add hard dependencies to the SDK.
- Do not use absolute paths in code or scripts.
- Do not commit .env files or secrets.
- Do not create outreach content without verifying the repo is public and package is installable.
- Do not mix implementation, testing, deployment, and strategy in one mega-session.
