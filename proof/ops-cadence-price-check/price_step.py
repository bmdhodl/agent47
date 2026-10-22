"""Write three runnable copies of the ops-cadence run block for local tests.

Each copy changes only what the case needs and fails if a substitution misses.
Needs PyYAML (`pip install pyyaml`); the SDK itself does not use it.
"""
from pathlib import Path
import sys

import yaml

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
workflow = yaml.safe_load((repo / ".github/workflows/ops-cadence.yml").read_text(encoding="utf-8"))
run = next(step["run"] for step in workflow["jobs"]["staleness"]["steps"] if "run" in step)


def swap(script, old, new):
    if script.count(old) != 1:
        raise SystemExit(f"expected one {old!r} in the run block")
    return script.replace(old, new)


base = swap(run, "DOW=$(date +%u)", "DOW=1  # test harness: force Monday")
base += 'echo "price_date=${price_date} price_age=${price_age}"\n'

table = (repo / "sdk/agentguard/price_table.py").read_text(encoding="utf-8")
broken = swap(table, '"last_updated": "', '"last_verified": "')
(out / "broken_price_table.py").write_text(broken, encoding="utf-8")

cases = {
    "today": base,
    "plus100": swap(base, "now=$(date +%s)", "now=$(( $(date +%s) + 100*86400 ))  # test harness: +100 days"),
    "broken-marker": swap(base, "sdk/agentguard/price_table.py)", '"$BROKEN_TABLE")'),
}
for name, script in cases.items():
    (out / f"step-{name}.sh").write_text(script, encoding="utf-8", newline="\n")
print("wrote", ", ".join(cases))
