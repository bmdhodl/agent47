"""Re-checks the site de-slop claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
# Nine pages ship in this PR; update the count when a page is added.
pages = [p for p in (ROOT / "site").rglob("*.html") if p.name != "security.html"]
assert len(pages) == 9, len(pages)
for page in pages:
    text = page.read_text(encoding="utf-8")
    assert "assets/site.css" in text, page.name
    assert "340%" not in text, page.name
    assert "script.async = true" in text and "isAllowedHost" in text, page.name
for line in (ROOT / "proof/landing-deslop/scan-after.txt").read_text().splitlines():
    assert "score=0.000" in line, line
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_enforcement_boundary.py", "sdk/tests/test_activation_evidence.py"],
    cwd=ROOT, check=True,
)
print("site claims hold")
