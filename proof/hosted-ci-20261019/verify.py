"""Verify that agent47 CI runs on GitHub-hosted runners and keeps its fork guard.

Run from the repository root: python proof/hosted-ci-20261019/verify.py
Exit 0 prints "Verified hosted CI"; any failure raises with the reason.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ("ci.yml", "actionlint.yml", "claude-review.yml", "codeql.yml", "docs-consistency.yml", "trustabl.yml")


def main() -> None:
    jobs = 0
    for filename in WORKFLOWS:
        workflow = yaml.safe_load((ROOT / ".github/workflows" / filename).read_text(encoding="utf-8"))
        for name, job in workflow["jobs"].items():
            if job["runs-on"] != "ubuntu-latest":
                raise SystemExit(f"{filename}:{name} runs on {job['runs-on']!r}, not ubuntu-latest")
            jobs += 1

    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    guard = ci["jobs"]["ci-required"]["steps"][0]
    if "github.event.pull_request.head.repo.full_name != github.repository" not in guard["if"]:
        raise SystemExit("ci-required no longer refuses fork heads first")
    if not guard["run"].rstrip().endswith("exit 1"):
        raise SystemExit("ci-required fork guard no longer fails the gate")

    print(f"Verified hosted CI: {jobs} jobs in {len(WORKFLOWS)} workflows run on ubuntu-latest; fork guard intact")


if __name__ == "__main__":
    main()
