"""Reproduce/verify the cross-process lock fix under heavy contention.

Run from anywhere in the repo:  python proof/issue-sweep-2026-06-06/stress_lock.py

Derives the SDK path from this file's location (repo_root/sdk) so it stays
reproducible on any checkout - no machine-specific paths.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# proof/issue-sweep-2026-06-06/stress_lock.py -> parents[2] == repo root
SDK = str(Path(__file__).resolve().parents[2] / "sdk")

WORKER = """
import sys
from agentguard import BudgetGuard, JsonFileStateStore, BudgetExceeded
path, ceiling, attempts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
guard = BudgetGuard(max_calls=ceiling, store=JsonFileStateStore(path), key="fleet")
ok = 0
for _ in range(attempts):
    try:
        guard.consume(calls=1); ok += 1
    except BudgetExceeded:
        break
print(ok)
"""

env = {**os.environ, "PYTHONPATH": SDK}
NPROC = 10
ATT = 60
CEIL = 150
fails = 0
for trial in range(20):
    d = tempfile.mkdtemp()
    try:
        path = os.path.join(d, "budget.json")
        procs = [
            subprocess.Popen(
                [sys.executable, "-c", WORKER, path, str(CEIL), str(ATT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            for _ in range(NPROC)
        ]
        outs = [p.communicate(timeout=120) for p in procs]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    rcs = [p.returncode for p in procs]
    succ = sum(int(o[0].strip().splitlines()[-1]) for o in outs if o[0].strip())
    bad = [(i, rcs[i], outs[i][1][-300:]) for i in range(NPROC) if rcs[i] != 0]
    status = "OK" if (all(r == 0 for r in rcs) and succ == CEIL) else "FAIL"
    if status == "FAIL":
        fails += 1
        print(f"trial {trial}: {status} successes={succ} (want {CEIL}) returncodes={rcs}")
        for i, rc, err in bad:
            print(f"   proc{i} rc={rc} stderr_tail={err!r}")
    else:
        print(f"trial {trial}: OK successes={succ} returncodes_all_zero")
print("TOTAL FAILS:", fails)
