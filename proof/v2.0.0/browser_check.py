"""Check the changed site pages at 375, 768 and 1440 px wide.

Each page must show its 2.0.0 release label as rendered (CSS capitalizes
the index labels), show no "2.0.0 candidate" or
"unpublished 2.0.0" text, and have no horizontal overflow.
Run from the repo root: python proof/v2.0.0/browser_check.py [site-dir]
Needs Playwright for Python with Chromium; the SDK does not use it.
"""
import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "site"
PAGES = {
    "index.html": ["Claude Code NEW IN 2.0.0", "Any Python script NEW IN 2.0.0",
                   "agentguard receipt is new in 2.0.0.",
                   "Since 2.0.0 it patches the OpenAI Responses API"],
    "enforcement.html": ["OpenAI Responses API and Agents SDK (2.0.0+)"],
    "blog/budget-limits-ai-agents.html": ["from 2.0.0, the Responses API",
                                          "From 2.0.0 it patches the Responses API too."],
    "blog/ai-agent-cost-overruns.html": ["From 2.0.0 the Responses API is patched too."],
}
BANNED = ["2.0.0 candidate", "unpublished 2.0.0"]
WIDTHS = [375, 768, 1440]

results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 900})
        for rel, expected in PAGES.items():
            page.goto((SITE / rel).as_uri())
            text = " ".join(page.inner_text("body").split())
            dims = page.evaluate(
                "() => ({width: window.innerWidth,"
                " scroll: document.documentElement.scrollWidth,"
                " body: document.body.scrollWidth})")
            missing = [e for e in expected if e not in text]
            banned = [b for b in BANNED if b.lower() in text.lower()]
            overflow = dims["scroll"] > dims["width"] or dims["body"] > dims["width"]
            results.append({"path": rel, "viewport": width, "dimensions": dims,
                            "missing": missing, "banned_found": banned,
                            "overflow": overflow,
                            "passed": not missing and not banned and not overflow})
            if rel == "index.html" and width in (375, 1440) and len(sys.argv) == 1:
                page.locator("#ways, .ways").first.scroll_into_view_if_needed()
                page.screenshot(path=str(OUT / f"browser-index-{width}.png"))
        page.close()
    browser.close()

(OUT / "browser-checks.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
failed = [r for r in results if not r["passed"]]
print(f"{len(results) - len(failed)} of {len(results)} page checks passed")
for r in failed:
    print("FAILED", r)
sys.exit(1 if failed else 0)
