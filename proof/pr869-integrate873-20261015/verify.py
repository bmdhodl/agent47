"""Verify the combined loop and fail-closed installer changes without extra plugins."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ["test_loop_maintenance_regressions.py", "test_hook_install_failure.py", "test_guards.py",
         "test_hooks.py", "test_instrument.py", "test_tracing.py", "test_receipt.py", "test_dx.py",
         "test_architecture.py", "test_documentation.py", "test_enforcement_boundary.py"]


def main():
    for relative in sys.argv[1:]:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"Missing declared artifact: {relative}")
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONPATH": str(ROOT / "sdk")}
    with tempfile.TemporaryDirectory(prefix="agentguard-combined-check-") as temporary:
        argv = [sys.executable, "-m", "pytest", *[f"sdk/tests/{name}" for name in TESTS],
                "-q", "--tb=short", "-p", "no:cacheprovider", "--basetemp", str(Path(temporary) / "pytest")]
        print("Command:", " ".join(argv), flush=True)
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, check=False,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", file=sys.stderr, flush=True)
        print("Exit code:", result.returncode, flush=True)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
