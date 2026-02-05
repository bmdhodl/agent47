# Roadmap (Now → Prototype)

## Tonight (postable prototype)
- [x] Verify demo script produces traces and report
- [x] Add guard tests (loop + budget)
- [x] Add README section: "What it means" (interpret report)
- [x] Create a short demo GIF or screenshot plan (optional)

## Near-term (1–2 weeks)
- [x] Deepen LangChain integration (real token usage + tool metadata)
- [x] Add simple JSON schema doc for trace events
- [x] Add replay tests + CLI report tests
- [x] Add minimal website or README badges
- [x] Wire Resend email capture (Vercel + destination email)
- [x] Add fast script to set env + deploy
- [x] Add one-command deploy + open script
- [x] Add end-to-end local test script (vercel dev + curl)
- [x] Auto-capture screenshot on each E2E test run
- [x] Prepare public launch post (LinkedIn/X + HN) with demo screenshot
- [x] Publish repo (README polish + badges + contribution guidelines)
- [x] Add issue templates for feedback collection
- [x] Add minimal code of conduct
- [x] Add CI workflow + badge
- [x] Add security policy
- [x] Add changelog
- [x] Add local trace viewer (browser UI)

## Blocked / Decisions Needed
- [x] Choose public repo URL (needed for badges + launch links)

## Execution Plan
- [x] Create aligned execution plan doc (docs/execution_plan.md)

## Phase 2: Ship & Distribute
- [x] PyPI-ready packaging (pyproject.toml metadata, publish workflow, install instructions)
- [x] TimeoutGuard (wall-clock time limit for agent runs)
- [x] HTTP Sink (batched trace ingestion for future hosted dashboard)
- [x] Real LangChain integration (BaseCallbackHandler, nested spans, guard wiring)
- [x] CI hardening (Python 3.9–3.12 matrix, ruff lint)
- [x] Blog post: "Why Your AI Agent Loops"
- [x] Loop failure demo (sdk/examples/loop_failure_demo.py)
- [x] Updated launch posts (LinkedIn/X + HN)
- [ ] Publish to PyPI (tag v0.2.0, needs PyPI account + PYPI_TOKEN secret)
- [ ] Post blog + HN launch
- [ ] Collect 5–10 design partners

## Phase 3: Hosted Dashboard (upcoming)
- [ ] Trace ingestion API (Vercel serverless, POST /api/ingest)
- [ ] Vercel Postgres schema (teams, api_keys, events)
- [ ] Dashboard UI (vanilla JS, trace list + detail views)
- [ ] API key provisioning
- [ ] Retention cleanup cron (7-day free tier)
- [ ] Stripe billing (after design partner validation)

## Decisions Made
- [x] Primary integration target: LangChain
- [x] Hosted direction: self-hosted first
- [x] Dashboard stack: Vanilla JS + Vercel API routes (not Next.js)
