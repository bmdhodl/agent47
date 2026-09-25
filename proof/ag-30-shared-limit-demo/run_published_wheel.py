"""Run the shared-limit demo against the published 1.4.0 wheel."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "examples" / "shared_call_limit.py"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "site"
        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "agentguard47==1.4.0",
                "--target",
                str(target),
                "--no-deps",
                "--disable-pip-version-check",
            ],
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            sys.stderr.write(install.stderr or install.stdout)
            raise SystemExit(install.returncode)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(target)
        env.pop("PYTHONSAFEPATH", None)
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import agentguard, importlib.metadata as m; "
                    "from pathlib import Path; "
                    "print(m.version('agentguard47')); "
                    "print(Path(agentguard.__file__).resolve())"
                ),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if probe.returncode != 0:
            sys.stderr.write(probe.stderr)
            raise SystemExit(probe.returncode)
        lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
        if len(lines) < 2 or lines[0] != "1.4.0":
            sys.stderr.write(probe.stdout)
            raise SystemExit(1)
        installed = Path(lines[1]).resolve()
        repo_init = (ROOT / "sdk" / "agentguard" / "__init__.py").resolve()
        if installed == repo_init or target.resolve() not in installed.parents:
            sys.stderr.write(probe.stdout)
            raise SystemExit("imported the checkout")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
        if '"dispatched": 1' not in completed.stdout or '"stopped": 1' not in completed.stdout:
            raise SystemExit(1)
        if "Not a provider invoice cap." not in completed.stdout:
            raise SystemExit(1)
        print("one_dispatch")


if __name__ == "__main__":
    main()
