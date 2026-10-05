"""Check that the weekly architecture reminder tracks the root ARCHITECTURE.md.

The root ARCHITECTURE.md owns module boundaries and data flow, and the agent
entry points (AGENTS.md, CLAUDE.md) check its age. ops/02-ARCHITECTURE.md keeps
the public export table, so the PR template still sends API changes there.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]


def text(path):
    return (repo / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


workflow = text(".github/workflows/ops-cadence.yml")
require("git log -1 --format=%ct -- ARCHITECTURE.md)" in workflow,
        "ops-cadence.yml does not measure the age of the root ARCHITECTURE.md")
require("Review \\`ARCHITECTURE.md\\` — any boundary changes?" in workflow,
        "ops-cadence.yml reminder does not name the root ARCHITECTURE.md")
require("ops/02-ARCHITECTURE.md" not in workflow, "ops-cadence.yml still tracks ops/02-ARCHITECTURE.md")

for entry_point in ("AGENTS.md", "CLAUDE.md"):
    require("ops/02-ARCHITECTURE.md" not in text(entry_point), f"{entry_point} checks a different architecture file")

template = text(".github/PULL_REQUEST_TEMPLATE.md")
require("If `__init__.py` exports changed, `ops/02-ARCHITECTURE.md` updated" in template,
        "PR template no longer sends export changes to the export table")
require("## Public API surface" in text("ops/02-ARCHITECTURE.md"), "ops/02-ARCHITECTURE.md lost its export table")

age = subprocess.run(["git", "log", "-1", "--format=%ct", "--", "ARCHITECTURE.md"], cwd=repo,
                     capture_output=True, text=True, check=True).stdout.strip()
require(age.isdigit(), "git has no commit time for ARCHITECTURE.md, so arch_age cannot be computed")

guard = subprocess.run([sys.executable, "scripts/review_readiness_guard.py"], cwd=repo,
                       capture_output=True, text=True, check=False)
require(guard.returncode == 0, "review readiness guard fails")

print("Verified architecture reminder targets")
