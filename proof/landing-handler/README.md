# Landing page: the handler

Design rules: [docs/site-design.md](../../docs/site-design.md), written for this
change. The landing page is rebuilt on them; the shared tokens change two
colors for contrast.

- Hero receipt is the real output of `agentguard receipt` on the offline demo
  (agentguard47 1.4.1 source). The barcode SVG is drawn from the same glyph
  line the CLI printed, one column per hex digit.
- The STOPPED stamp sits on the barcode, which is decorative. The crosshair
  circles the receipt's own STOPPED line. Case-file cards are stamped only for
  the three limits the demo actually stopped; the time card is not.
- Commands that are not on PyPI yet (`hook`, `run`, `receipt`) are labeled
  "new in 1.4.1".
- Contrast: `--tie-bright` moved from #e0323d (4.4:1 on black) to #ea4049
  (5.0:1); `--steel-dark` from #6f6862 (3.6:1) to #8a827c (5.2:1).

Evidence:
- `measure.py`: re-renders every page in headless Chromium at 1440, 768, and
  375 px and re-runs the slop scan on the current files. `verify.py` calls it,
  so the claims are checked against the site as it is, not the recorded output.
- `scan.txt`, `site-slop.json`: defluff 0.000 on every page.
- `scrollwidth.txt`: no horizontal scroll at 1440, 768, 375 on seven pages.
- `screens/`: full landing at 1440 and the hero at 1440 and 375.
- `checks.txt`: repo checks.
