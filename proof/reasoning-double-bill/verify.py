"""Re-runs the reasoning double-bill tests. Exit 0 means they pass."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_precision_cost.py", "sdk/tests/test_real_dispatch.py"],
    cwd=ROOT, check=True,
)
