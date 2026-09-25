"""Run installed CLI paths in a temporary workspace, never a source checkout."""
import json
import os
import subprocess
import sys
import tempfile
from importlib.metadata import version

import agentguard

env = dict(os.environ)
env.pop("PYTHONPATH", None)
results = []
with tempfile.TemporaryDirectory() as workspace:
    for args in ([], ["doctor"], ["demo", "--trace-file", "demo.jsonl"],
                 ["report", "demo.jsonl", "--json"],
                 ["incident", "demo.jsonl"],
                 ["quickstart", "--framework", "raw", "--write", "--output", "starter.py"],
                 ["badge"]):
        proc = subprocess.run([sys.executable, "-m", "agentguard", *args],
                              cwd=workspace, env=env, capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, (args, proc.stdout, proc.stderr)
        results.append({"args": args, "exit": proc.returncode})
    proc = subprocess.run([sys.executable, "starter.py"], cwd=workspace, env=env,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    results.append({"args": ["starter.py"], "exit": proc.returncode})
assert "site-packages" in agentguard.__file__
print(json.dumps({"version": version("agentguard47"), "python": sys.version,
                  "import_path": agentguard.__file__, "results": results}, indent=2))
