"""Check that the ops-cadence price-age check reads the real price table date.

Since #792 the date lives in DEFAULT_PRICE_TABLE["last_updated"] in
sdk/agentguard/price_table.py. cost.py only aliases it, so a sed for a literal
LAST_UPDATED line in cost.py printed nothing and the check always warned.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
proof = Path(__file__).resolve().parent


def text(path):
    return (repo / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


workflow = text(".github/workflows/ops-cadence.yml")
require("sdk/agentguard/price_table.py)" in workflow, "ops-cadence.yml does not read the date from price_table.py")
require("LAST_UPDATED" not in workflow, "ops-cadence.yml still names the LAST_UPDATED alias")
require("sdk/agentguard/cost.py" not in workflow, "ops-cadence.yml still sends readers to cost.py")
require("fix its price check" not in text("ops/FOLLOWUP.md"), "ops/FOLLOWUP.md still lists the price check defect")

test = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_ci_guardrails.py::test_ops_cadence_reads_the_price_table_date"],
    cwd=repo, capture_output=True, text=True, check=False,
)
require(test.returncode == 0, "the ops-cadence price date regression test fails")

# Saved by running the workflow run block in Git Bash with gh stubbed.
step = (proof / "01-workflow-step.txt").read_text(encoding="utf-8")
cases = step.split("=== ")
today = next((case for case in cases if case.startswith("today")), "")
later = next((case for case in cases if case.startswith("plus100")), "")
broken = next((case for case in cases if case.startswith("broken-marker")), "")
date = text("sdk/agentguard/price_table.py").split('"last_updated": "', 1)[1].split('"', 1)[0]
require(f"price_date={date}" in today and "Could not parse" not in today and "exit=0" in today,
        "the saved run for today did not parse the price table date")
require("days since last hand-verify" in later and "exit=0" in later,
        "the saved run at +100 days did not ask for a price re-verify")
require("Could not parse last_updated" in broken and "missing or unparseable" in broken,
        "the saved run with a broken marker did not warn")

guard = subprocess.run([sys.executable, "scripts/review_readiness_guard.py"], cwd=repo,
                       capture_output=True, text=True, check=False)
require(guard.returncode == 0, "review readiness guard fails")

print("Verified ops-cadence price check")
