# AgentGuard47 Landing Brand Proof

Date: 2026-05-31

## Scope

- Synced `site/index.html`, the public SDK repo's static reference copy, to the deployed AgentGuard47 homepage from the dashboard repo.
- Kept the page scoped to the public SDK: local-first runtime budget, loop, retry, and timeout enforcement first; hosted dashboard only after local proof.
- Avoided protected character/logo assets. The direction uses a black, white, red, and steel palette with a terminal/proof motif.

## Conversion Research Notes

- Current SaaS landing-page guidance consistently favors clear above-fold value, one primary CTA, early proof, mobile-first layout, and visible product outcomes.
- Sources reviewed:
  - InBuild SaaS landing guide: hero promise, CTA, proof, feature blocks, FAQ, and final CTA.
  - Woobox landing-page checklist: clarity, CTA visibility, specific proof, and shorter forms.
  - Developer-tool landing examples such as Vale and OpenBoot: command-first install proof and local trust cues.

## Verification

- `site/index.html` parses with Python `HTMLParser`.
- `site/index.html` is ASCII-only.
- `python scripts/sdk_preflight.py` reported no SDK-relevant checks for this static-site-only diff.
- `git diff --check` passed.
- Playwright screenshots captured:
  - `desktop.png` at `1440x1100`
  - `mobile.png` at `390x844`

## Manual Visual Checks

- Desktop first viewport shows the brand mark, primary install CTA, GitHub CTA, proof stats, terminal proof scene, and a visible hint of the next section.
- Mobile first viewport shows the install CTA, 60-second proof CTA, install command, compact terminal proof scene, and a visible hint of the next section.
