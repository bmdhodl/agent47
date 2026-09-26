"""Re-checks the price-table claims. Exit 0 means all hold."""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_price_table.py", "sdk/tests/test_cost.py", "sdk/tests/test_precision_cost.py",
     "sdk/tests/test_sdk_release_guard.py", "sdk/tests/test_reservation_stream.py"],
    cwd=ROOT, check=True,
)
after = subprocess.run(
    [sys.executable, "proof/price-table-accuracy/compare.py"], cwd=ROOT, check=True,
    capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "sdk")},
).stdout
rows = [line for line in after.splitlines()[1:] if "unknown" not in line]
assert rows and all(" 1.00x " in line for line in rows), after
before = (ROOT / "proof/price-table-accuracy/before-fix.txt").read_text(encoding="utf-8")
assert "0.50x  computed" in before and "136.96x" in before
print("price-table claims hold")
