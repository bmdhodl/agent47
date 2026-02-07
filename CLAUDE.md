# CLAUDE.md — AgentGuard (agent47)

## What This Is

AgentGuard is a lightweight observability and evaluation SDK for multi-agent AI systems. The SDK is open source (MIT); the hosted dashboard is the commercial layer.

- **Repo:** github.com/bmdhodl/agent47
- **Package:** `agentguard47` on PyPI (v0.4.0)
- **Landing page:** site/index.html (deployed via Vercel)

## Architecture

```
agent47/
├── sdk/                     # Python SDK (the OSS product)
│   ├── agentguard/          # Source — zero dependencies, stdlib only
│   │   ├── tracing.py       # Tracer, TraceSink, TraceContext, JsonlFileSink, StdoutSink
│   │   ├── guards.py        # LoopGuard, BudgetGuard, TimeoutGuard + exceptions
│   │   ├── recording.py     # Recorder, Replayer (deterministic replay)
│   │   ├── evaluation.py    # EvalSuite — chainable assertion-based trace analysis
│   │   ├── instrument.py    # @trace_agent, @trace_tool, patch_openai, patch_anthropic
│   │   ├── viewer.py        # Gantt trace viewer (self-contained HTML + stdlib HTTP server)
│   │   ├── cli.py           # CLI: report, summarize, view, eval
│   │   ├── sinks/           # HttpSink (batched background thread)
│   │   └── integrations/    # LangChain BaseCallbackHandler
│   ├── tests/               # 48 tests, unittest
│   ├── examples/            # demo_agent.py + sample traces.jsonl
│   └── pyproject.toml       # Package config
├── dashboard/               # Hosted dashboard (Next.js) — THE COMMERCIAL LAYER
├── api/                     # Vercel serverless functions
│   └── lead.js              # Email capture endpoint
├── site/                    # Landing page (static HTML)
├── scripts/                 # deploy.sh, run_demo.sh, e2e_test.sh
├── docs/
│   ├── strategy/            # prd.md, architecture.md, pricing.md, etc.
│   └── outreach/            # Distribution drafts
└── .github/workflows/       # ci.yml, publish.yml, scout.yml
```

## SDK Conventions

- **Zero dependencies.** The SDK uses only Python stdlib. Optional deps (langchain-core) are extras.
- **Python 3.9+** compatibility. CI tests 3.9, 3.10, 3.11, 3.12.
- **Trace format:** JSONL. Each line is a JSON object with: service, kind (span/event), phase (start/end/emit), trace_id, span_id, parent_id, name, ts, duration_ms, data, error.
- **Guards raise exceptions:** LoopDetected, BudgetExceeded, TimeoutExceeded.
- **TraceSink interface:** All sinks implement `emit(event: Dict)`. Built-in: StdoutSink, JsonlFileSink, HttpSink.
- **Exports:** All public API surfaces through `agentguard/__init__.py`.

## Testing

```bash
# From repo root:
PYTHONPATH=sdk python3 -m unittest discover -s sdk/tests -v

# Lint:
ruff check sdk/agentguard/
```

- All tests use `unittest` (no pytest dependency).
- Test files: test_guards.py, test_recording.py, test_tracing.py, test_cli_report.py, test_http_sink.py, test_langchain_integration.py, test_evaluation.py, test_instrument.py, test_viewer.py.

## Publishing

```bash
# Bump version in sdk/pyproject.toml
# Update CHANGELOG.md
# Commit, tag, push:
git tag v0.X.0 && git push origin v0.X.0
# publish.yml triggers automatically on v* tags → PyPI
```

- Package name: `agentguard47` (not `agentguard` — that was taken)
- Auth: API token via PYPI_TOKEN secret (not OIDC — repo was private when first published)

## CI/CD

- **ci.yml:** Python 3.9-3.12 matrix + ruff lint. Runs on push to main and PRs.
- **publish.yml:** Builds and publishes to PyPI on v* tags.
- **scout.yml:** Daily cron (9am EST) — searches GitHub for fresh issues mentioning agent loops/observability, creates a GitHub Issue with outreach targets.

## Dashboard (Commercial Layer)

The dashboard is the monetization path. Stack: **Next.js 14 (App Router) + direct Postgres + NextAuth + Stripe**.

**Architecture:**
- `dashboard/src/lib/db.ts` — Direct Postgres via `postgres` (postgresjs), connects via `DATABASE_URL`
- `dashboard/src/lib/next-auth.ts` — NextAuth credentials provider with bcrypt password hashing
- `dashboard/src/app/api/ingest/route.ts` — THE critical endpoint. Accepts NDJSON from HttpSink, validates with Zod, stores in `events` table, increments usage.
- `dashboard/src/app/api/keys/` — API key generation (ag_ prefix, SHA-256 hashed) and revocation
- `dashboard/src/components/trace-gantt.tsx` — React port of viewer.py Gantt JS
- `dashboard/src/app/api/billing/` — Stripe checkout, portal, webhook
- `dashboard/src/app/api/cron/retention/` — Vercel cron: deletes events past plan retention window

**Database tables:** `users`, `teams`, `api_keys`, `events`, `usage`

**Pricing:**
- Free: 10K events/month, 7-day retention, 2 keys
- Pro: $39/month, 500K events, 30-day retention, 5 keys
- Team: $149/month, 5M events, 90-day retention, 20 keys, 10 users

**No Supabase JS client.** We use the Supabase-hosted Postgres directly via connection string. Auth is NextAuth with credentials provider, not Supabase Auth.

## Key Decisions

- The SDK is the acquisition channel. It must stay free, MIT, zero-dependency.
- The dashboard is the paywall. Users who outgrow local JSONL files upgrade.
- HttpSink already exists — it's the bridge. Point it at the dashboard API and traces flow automatically.
- No vendor lock-in: users can always export to JSONL and use the local CLI.

## What NOT To Do

- Do not add hard dependencies to the SDK. Ever.
- Do not use absolute paths in code or scripts.
- Do not commit .env files or secrets.
- Do not create outreach content without verifying the repo is public and the package is installable.
- Do not mix implementation, testing, deployment, and strategy in one mega-session.
