"""Re-checks the receipt claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "sdk/tests/test_receipt.py"],
    cwd=ROOT, check=True,
)
text = (ROOT / "proof/receipt/demo-receipt.txt").read_text(encoding="utf-8")
assert "STOPPED" in text and "guard stops                            3" in text
(ROOT / "proof/receipt/demo-receipt-cp1252.txt").read_bytes().decode("cp1252")
print("receipt claims hold")
