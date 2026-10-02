"""Re-checks the LangChain cost claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_langchain_integration.py"],
    cwd=ROOT, check=True,
)
before = (ROOT / "proof/langchain-cost/before-fix.txt").read_text(encoding="utf-8")
assert "test_unknown_model_trips_a_dollar_budget" in before and "3 failed" in before
print("langchain cost claims hold")
