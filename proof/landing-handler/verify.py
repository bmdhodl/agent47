"""Re-checks the landing claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
index = (ROOT / "site/index.html").read_text(encoding="utf-8")
receipt = (ROOT / "proof/receipt/demo-receipt.txt").read_text(encoding="utf-8")
for line in ("budget  $1.08 over $1.00", "loop    search x3, same args", "retry   fetch_docs 3 tries, limit 2"):
    assert line in receipt and line in index, line
assert index.count('class="mark"') == 3
assert index.count("new in 1.4.1") == 2
assert all("score=0.000" in line for line in (ROOT / "proof/landing-handler/scan.txt").read_text().splitlines())
widths = (ROOT / "proof/landing-handler/scrollwidth.txt").read_text().splitlines()
assert all(line.split()[1] == line.split()[3] for line in widths), widths
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_enforcement_boundary.py", "sdk/tests/test_activation_evidence.py"],
    cwd=ROOT, check=True,
)
print("landing claims hold")
