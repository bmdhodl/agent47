# BMD rendered design

`DESIGN.md` v1.2.0 is the shared authority. `design-tokens.css` and
`design-tokens.json` are its generated exports. The approved loop tile is
`bmd-loop-mark-512.png`; tests pin its canonical SHA-256.

`design-surfaces.css` adapts the shared tokens to this product. Run
`python scripts/sync_design_assets.py` after an export or presentation change.
The generated Python module embeds CSS and the raster mark so standalone HTML
works offline and installed packages need no asset server or runtime dependency.
The module, generated tokens, and served copies are checked for drift.

## Acceptance

- `python scripts/check_rendered_design.py` exercises real renderer output and
  rejects missing or altered branding. These regressions failed before the fix.
- `npm run test:e2e` uses the dev-only Python Playwright dependency to render
  maintained surfaces at 375, 768 and 1440. It checks logo loading, boundaries,
  readable type, text contrast, keyboard entry, reduced motion, overflow and
  200% CSS zoom. Screenshots and reading counts go to `output/playwright/`.
- Automated checks do not certify comprehension. A reviewer must still identify
  purpose, state and next action. Root-task visual review is separate evidence.
- Historical screenshots, release videos and exported reports remain historical.
  Regeneration uses the new design. This PR does not publish or deploy a product.

## Maintained sources

All nine content pages under `site/`, the security redirect fallback, and
`sdk/agentguard/reporting.py` use the shared identity. The homepage has 399
default-visible main-content words, counted from rendered `innerText`. The
receipt contains factual sample data; long guides are documentation, not
marketing-page budget exceptions. The existing stamp transition remains and
stops with reduced motion. No established orange particle animation was removed.

The old handler treatment is retained in `docs/archive/site-handler.md` as
history. `site/README.md` says the deployed landing page is owned by the retired
dashboard checkout. That source/deployment ownership remains unresolved; local
tests do not claim that the public domain changed. The retired app is untouched.
Release-email content uses the central bmdpat email renderer, outside this repo.
