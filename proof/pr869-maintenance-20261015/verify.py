"""Re-run local behavioral acceptance without unrelated third-party pytest plugins."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TESTS = ["test_loop_maintenance_regressions.py", "test_guards.py", "test_hooks.py",
         "test_instrument.py", "test_tracing.py", "test_receipt.py"]


def main():
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    with tempfile.TemporaryDirectory(prefix="agentguard-loop-check-") as tmp:
        args = [sys.executable, "-m", "pytest", *[f"sdk/tests/{test}" for test in TESTS],
                "-q", "--tb=short", "--basetemp", str(Path(tmp) / "pytest")]
        print("Command:", " ".join(args), flush=True)
        result = subprocess.run(args, cwd=ROOT, env=env, check=False, capture_output=True, text=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", file=sys.stderr, flush=True)
        print(f"Exit code: {result.returncode}", flush=True)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
