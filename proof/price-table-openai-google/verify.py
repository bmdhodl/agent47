"""Re-checks the OpenAI and Gemini price claims offline. Exit 0 means all hold."""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_price_table.py", "sdk/tests/test_cost.py",
     "sdk/tests/test_precision_cost.py", "sdk/tests/test_reservation_stream.py"],
    cwd=ROOT, check=True,
)
after = subprocess.run(
    [sys.executable, "proof/price-table-openai-google/compare.py"], cwd=ROOT, check=True,
    capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "sdk")},
).stdout
rows = after.splitlines()[1:]
assert rows and all(" 1.00x  computed" in line for line in rows), after
before = (ROOT / "proof/price-table-openai-google/before-fix.txt").read_text(encoding="utf-8")
assert "80.77x  overestimate" in before and "0.47x  computed" in before
live = (ROOT / "proof/price-table-openai-google/live-smoke.txt").read_text(encoding="utf-8")
assert "calls 4 |" in live
print("openai/gemini price claims hold")
