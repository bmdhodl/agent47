# Site de-slop and redesign

All pages under `site/` now share `site/assets/site.css` (black, off-white, red;
Archivo condensed + IBM Plex). The landing hero shows a receipt from the real
offline demo, with a barcode.

## Copy fixes

- `compare.html` showed `patch_openai(tracer)` with a guard in `Tracer(guards=...)`
  and said "agent stops at $5". Against the real OpenAI client that sends every
  call and records $0. The page now passes `budget_guard=`; the same check stops
  on the call that crosses $5 (four sends at $1.50, $6.00 recorded, fifth never
  sent). `test_site_patch_examples_pass_a_budget_guard` keeps it that way.
- Removed: "kills agents mid-run", "Hard budget enforcement: Yes", February 2026
  competitor pricing, "No cross-tenant access possible", "SDK v1.2.13" date line,
  and the unsourced "cost overruns average 340%" stat in two blog posts.
- Trust page SDK rows re-checked against source (network code, trace contents,
  HttpSink behavior).

## Evidence

- `site-slop-before.json` / `site-slop-after.json`, `scan-after.txt`:
  defluff score 0.000 on every page (was 0.001 on two).
- `checks.txt`: 1208 passed, docs, review-readiness, release guard, preflight.
- `screens/`: 1440 and 375 px. `scrollWidth` equals viewport on all nine pages
  at 1440, 768, and 375.

Out of scope: the hosted dashboard UI lives in the private repo.
