"""Re-checks the hook and run claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_hooks.py", "sdk/tests/test_runner.py", "sdk/tests/test_enforcement_boundary.py"],
    cwd=ROOT, check=True,
)
real = (ROOT / "proof/claude-code-hook/real-claude-run.txt").read_text(encoding="utf-8")
assert "2.1.283 (Claude Code)" in real
assert "the same call just ran 2 times in a row" in real
assert "the same call already failed 2 times" in real
run = (ROOT / "proof/agentguard-run/budget-stop.txt").read_text(encoding="utf-8")
assert "stopped the run. Cost budget exceeded" in run and run.rstrip().endswith("exit 1")
print("hook and run claims hold")
