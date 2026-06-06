# Onboarding-funnel fix — change log + proof

Scope: `site/` only (static public site). No SDK/runtime code touched, so the
zero-dep core, public API, and test suite are unchanged. These changes fix the
broken onboarding funnel and stale data found in Checkpoint 5, and add a
frictionless quickstart page with a README-badge network-effect loop.

## Files changed

| File | Change | Finding fixed |
|------|--------|---------------|
| `site/quickstart.html` | **New page.** Real `pip install → doctor → demo → report → quickstart` flow with copy buttons, a 6-framework starter grid (matches the CLI exactly), the real `agentguard.init` snippet, and a copyable "Guarded by AgentGuard47" README badge. | #1 (homepage `/quickstart` CTA had no target) |
| `site/index.html` | Nav + footer: `/pricing` → `/compare#pricing`; added `Compare` link. | #2, #3 |
| `site/compare.html` | Added `id="pricing"` to the pricing table; nav + footer link to `/quickstart`; footer `/#pricing` → `#pricing`. | #3, #6 |
| `site/trust.html` | Moved **gzip**, **retry+idempotency**, **429/Retry-After backpressure** from *Planned* to *Current* (all shipped in `HttpSink`); "Last updated" → June 2026 (v1.2.13); footer `/index.html#pricing` → `/compare#pricing`; added Home/Quickstart. | #4, #5 |
| `site/blog/*.html` (×3) | `/blog/` → `https://bmdpat.com/blog` (no in-repo blog index existed); `/#pricing` → `/compare#pricing`. | new (caught by link checker) |
| `site/sitemap.xml` | Added `/quickstart`; refreshed `lastmod` on changed pages. | SEO hygiene |

## Why this enhancement (not a new SDK feature)

`memory/` is explicit: **distribution > features**, and the #1 gap is "convert
installs into visible proof" (3 GitHub stars vs thousands of PyPI downloads).
The most leverage, lowest risk, and most in-scope move is to repair the
onboarding funnel the homepage already advertises and add a viral primitive
(the README badge → every adopter repo links back). No speculative guard, no
new runtime dependency, no dashboard work — fully inside the SDK/site boundary.

## Proof (re-runnable)

- `06-link-integrity.txt` — 8 pages, 53 internal links: **all resolve, all
  `#anchors` exist** (was 6 broken before the fix).
- `05-site-snippets.txt` — the `index.html` and `compare.html` code examples
  execute against the real SDK.
- Blog snippet APIs verified live: `LoopGuard(max_repeats=, window=)`,
  `patch_openai(..., budget_guard=)`, `Tracer(service=, guards=[...])` all valid.
- Visual: `quickstart.html` rendered in the preview server — hero, 4-step proof
  path, framework grid, syntax-highlighted snippet, live shields.io badge, and
  Star-on-GitHub CTA all display; badge image `complete = true`; 0 console errors.

## Review round 2 — Vercel routing fix (Codex P2)

The first pass used clean URLs (`/compare`, `/quickstart`). But `vercel.json`
rewrites `/(.*)` → `/site/$1` with `cleanUrls` **unset (defaults false)**, so a
clean path resolves to `/site/compare` — and the file is `site/compare.html`, so
it 404s. Enabling `cleanUrls` was rejected: it would 308-redirect the existing
`.html` links (compare/blog footers) to clean paths, which the catch-all rewrite
then turns into `/site/site/...` → 404.

Fix: every internal page link now uses the explicit `.html` form
(`/compare.html#pricing`, `/quickstart.html`, `/trust.html`). `/x.html` →
`/site/x.html` exists unconditionally. Also updated `quickstart.html` canonical +
`og:url` and the sitemap `quickstart` entry to `.html`.

Proof: `07-link-integrity-vercel-accurate.txt` re-checks all 53 links against the
**exact** `vercel.json` routing model (no `.html` guessing) → all resolve.

## Deferred (noted, not changed)

- #6 `security.html` is a redirect to `trust.html` (intentional); left as-is.
- #7 CLI `quickstart` lacks a `pydantic_ai` framework although a
  `examples/starters/agentguard_pydantic_ai_quickstart.py` exists. Cosmetic;
  the quickstart page lists only the 6 CLI-supported frameworks to stay honest.
- #8 root `QA_REPORT.md` / `WORK_PLAN.md` from a prior PR violate the
  "no one-off reports in repo root" rule in `CLAUDE.md`. Out of scope for this
  change; flagged for a follow-up cleanup.
- `mcp-server` `hono` transitive advisory — routine `@modelcontextprotocol/sdk`
  bump, not reachable over stdio.
