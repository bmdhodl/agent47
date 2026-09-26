"""Measure the current site: defluff slop score and horizontal overflow.

Renders every page in headless Chromium at 1440, 768, and 375 px with the
network blocked (fonts fall back), and asserts scrollWidth equals the viewport.
Exit 0 means every page scores 0.000 and none scrolls sideways.
"""
import html
import re
import sys
from pathlib import Path

import defluff
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def visible_text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|pre|code)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


pages = sorted(p for p in SITE.rglob("*.html") if p.name != "security.html")
lexicon = defluff.load_lexicon(no_project_overlay=True)
failures = []
for path in pages:
    score = defluff.detect(visible_text(path.read_text(encoding="utf-8")), lexicon=lexicon).slop_score
    if score > 0:
        failures.append(f"{path.name}: slop {score:.3f}")

with sync_playwright() as p:
    browser = p.chromium.launch(**({"executable_path": CHROMIUM} if Path(CHROMIUM).exists() else {}))
    for path in pages:
        for width in (1440, 768, 375):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file:") else r.abort())
            page.goto(path.as_uri())
            scroll = page.evaluate("document.documentElement.scrollWidth")
            if scroll != width:
                failures.append(f"{path.name} at {width}px: scrollWidth {scroll}")
            page.close()
    browser.close()

print("\n".join(failures) or f"{len(pages)} pages: slop 0.000, no horizontal scroll at 1440/768/375")
sys.exit(1 if failures else 0)
