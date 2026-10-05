"""Check that the prompt-audit cleanup still holds in this checkout.

Each check ties an instruction-file fix to the repo fact that makes it true,
so a later edit that reintroduces a broken reference fails here.
"""
from pathlib import Path
import re
import subprocess
import sys

proof = Path(__file__).resolve().parent
repo = proof.parents[1]


def text(path):
    return (repo / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


agents = text("AGENTS.md")
require(".Codex/agents/" not in agents, "AGENTS.md still points to .Codex/agents/")
for ref in sorted(set(re.findall(r"\.claude/agents/[\w-]+\.md", agents))):
    require((repo / ref).is_file(), f"AGENTS.md references a missing file: {ref}")
require("PYPI_TOKEN" not in agents, "AGENTS.md still names PYPI_TOKEN")
require("id-token: write" in text(".github/workflows/publish.yml"),
        "publish.yml no longer uses Trusted Publishing")

sdk_dev = text(".claude/agents/sdk-dev.md")
pm = text(".claude/agents/pm.md")
for name, body in (("sdk-dev", sdk_dev), ("pm", pm)):
    match = re.match(r"---\r?\nname: ([\w-]+)\r?\ndescription: .+\r?\n---", body)
    require(match and match.group(1) == name, f"{name}.md lacks name/description frontmatter")
require((repo / ".claude/agents/../../GOLDEN_PRINCIPLES.md").resolve().is_file(),
        "sdk-dev.md link to GOLDEN_PRINCIPLES.md does not resolve")
require("../../GOLDEN_PRINCIPLES.md" in sdk_dev, "sdk-dev.md lost the fixed link")
require("RateLimitExceeded" not in sdk_dev and "MODEL_PRICES" not in sdk_dev,
        "sdk-dev.md names an SDK symbol that does not exist")
sdk_source = "\n".join(p.read_text(encoding="utf-8") for p in (repo / "sdk/agentguard").rglob("*.py"))
require(re.search(r"^class RetryLimitExceeded\b", sdk_source, re.M), "RetryLimitExceeded is gone from the SDK")
require(re.search(r"^DEFAULT_PRICE_TABLE\b", text("sdk/agentguard/price_table.py"), re.M),
        "DEFAULT_PRICE_TABLE is gone from price_table.py")

require("v1.2.6" not in pm, "pm.md still names v1.2.6 as the latest release")
require("AG-06 (#735) stays held" not in text(".agents/skills/next-ticket/SKILL.md"),
        "next-ticket still holds AG-06")
marketing = text(".claude/agents/marketing.md")
require("Phase 1" not in marketing and "#729" in marketing, "marketing.md still follows the old phase plan")
require(not re.search(r"\$\d", text(".claude/agents/dashboard-dev.md")), "dashboard-dev.md shows plan prices")

for name in ("01-preflight", "02-ci-tools-guard", "03-review-readiness", "04-lint", "05-structural",
             "06-security", "07-release-guard", "08-pypi-readme-check", "09-test"):
    require(text(f"proof/prompt-audit-cleanup/{name}.txt").rstrip().endswith("exit=0"), f"{name} did not exit 0")
require("1591 passed, 3 skipped" in text("proof/prompt-audit-cleanup/09-test.txt"), "test summary changed")

guard = subprocess.run([sys.executable, "scripts/sdk_release_guard.py"], cwd=repo,
                       capture_output=True, text=True, check=False)
require(guard.returncode == 0 and "Release guard passed" in guard.stdout, "release guard fails")

print("Verified prompt-audit cleanup")
