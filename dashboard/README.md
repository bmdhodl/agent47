# AgentGuard Dashboard

The hosted SaaS dashboard for AgentGuard. Provides trace visualization, cost tracking, guard alerts, usage monitoring, billing, and team management.

## What It Does

- **Trace viewer** — Gantt timeline visualization of agent runs
- **Cost dashboard** — Per-model cost breakdown and monthly trends
- **Guard alerts** — Loop detection, budget exceeded, and error notifications
- **Usage tracking** — Event counts, quota monitoring, retention enforcement
- **Billing** — Stripe-powered plans (Free, Pro, Team)
- **API key management** — `ag_` prefixed keys with SHA-256 hashed storage
- **Shared traces** — Public links with optional expiry for debugging collaboration

## Tech Stack

- **Next.js 14** (App Router, server components)
- **Postgres** via `postgres` npm package (direct connection, not Supabase JS)
- **NextAuth 4** (credentials provider, bcryptjs, JWT sessions)
- **Stripe** (checkout, customer portal, webhooks)
- **Zod** (request validation)
- **Vercel** (hosting, cron)

## Environment Variables

```bash
DATABASE_URL=postgresql://...          # Direct Postgres connection
NEXTAUTH_SECRET=...                    # JWT signing (openssl rand -base64 32)
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_TEAM=price_...
CRON_SECRET=...                        # Vercel cron auth
```

## Dev Commands

```bash
npm ci          # Install dependencies
npm run dev     # Dev server on localhost:3000
npm run build   # Production build
npm run lint    # ESLint (next lint)
```

## Key Directories

```
src/
├── app/
│   ├── api/ingest/     # Ingest endpoint (SDK HttpSink target)
│   ├── api/v1/         # Versioned read API (traces, alerts, usage, costs)
│   ├── api/billing/    # Stripe checkout, portal, webhook
│   ├── api/cron/       # Daily retention cleanup
│   ├── (auth)/         # Login, signup (public)
│   ├── (dashboard)/    # Protected pages: traces, costs, usage, alerts, settings
│   └── share/          # Public shared trace pages
├── lib/                # DB, auth, queries, validation, plans, Stripe, API keys
└── components/         # UI components (trace Gantt, share button, etc.)
```

## Deploy

Auto-deployed via `.github/workflows/deploy.yml` on push to `main`. PR previews also deployed automatically.
