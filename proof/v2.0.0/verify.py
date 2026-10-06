"""Re-check the v2.0.0 release prep. Run from the repo root: python proof/v2.0.0/verify.py"""
import json
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PUBLIC = ["README.md", "sdk/PYPI_README.md", "docs", "site", "examples"]
STALE = re.compile(r"2\.0\.0 candidate|unpublished (AgentGuard )?(\*\*)?2\.0\.0|not published yet"
                   r"|Unreleased candidate", re.IGNORECASE)
problems = []


def check(ok, message):
    if not ok:
        problems.append(message)


changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
first = re.search(r"^## (.+)$", changelog, re.M)
check(first is not None and first.group(1).strip() == "2.0.0", "CHANGELOG must open with the 2.0.0 section")
check("Unreleased candidate" not in changelog, "CHANGELOG still calls 2.0.0 an unreleased candidate")

for entry in PUBLIC:
    root = REPO / entry
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.suffix in {".md", ".html", ".py"}]
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if STALE.search(line):
                problems.append(f"{path.relative_to(REPO)}:{number} still has candidate wording")

decisions = (REPO / "memory/decisions.md").read_text(encoding="utf-8")
check("## 2.0.0 publication approval (2026-10-05)" in decisions, "memory/decisions.md lacks the release approval")
check("PyPI remains 1.4.0 until that publish finishes." in (REPO / "memory/state.md").read_text(encoding="utf-8"),
      "memory/state.md does not record the release timing")

for command in (["python", "scripts/sdk_release_guard.py"],
                ["python", "-m", "pytest", "sdk/tests/test_pypi_readme_sync.py", "-q", "-p", "no:cacheprovider"]):
    run = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    check(run.returncode == 0, f"{' '.join(command)} exited {run.returncode}")

log = (HERE / "10-clean-install.txt").read_text(encoding="utf-8")
exits = re.findall(r"^exit=(\d+)$", log, re.M)
check(len(exits) == 17 and set(exits[:-1]) == {"0"} and exits[-1] == "1",
      f"clean install expected 16 passes then one refusal, got {exits}")
check("agentguard 2.0.0" in log, "agentguard --version did not print 2.0.0")
check("requires a different Python: 3.10.11 not in '>=3.11'" in log, "Python 3.10 did not refuse the wheel")
check("sha256 of trace - agentguard47 2.0.0" in log, "receipt did not name agentguard47 2.0.0")

pages = json.loads((HERE / "browser-checks.json").read_text(encoding="utf-8"))
check(len(pages) == 12 and all(p["passed"] for p in pages), "browser checks did not all pass")

tests = (HERE / "09-test.txt").read_text(encoding="utf-8")
check(re.search(r"\b1592 passed, 3 skipped\b", tests) is not None and "exit=0" in tests, "full suite result changed")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("Verified v2.0.0 release prep")
