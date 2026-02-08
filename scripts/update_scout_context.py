#!/usr/bin/env python3
"""Generate scout_context.json from pyproject.toml, README.md, and git log.

Zero maintenance: all dynamic data is parsed from existing sources of truth.
  - Version + package name → sdk/pyproject.toml
  - Feature bullets → README.md ## Features section
  - What's new → git log since last tag (or last 5 commits)
  - Code snippets → hardcoded API surface (validated by tests/test_scout.py)

Run from repo root:
    python scripts/update_scout_context.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_version() -> tuple[str, str]:
    """Read version and package name from pyproject.toml."""
    path = os.path.join(REPO_ROOT, "sdk", "pyproject.toml")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"], data["project"]["name"]


def read_features() -> list[str]:
    """Parse feature bullets from README.md ## Features section."""
    path = os.path.join(REPO_ROOT, "README.md")
    with open(path) as f:
        content = f.read()

    # Extract the ## Features section
    match = re.search(r"## Features\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return ["Zero-dependency runtime guardrails for AI agents"]

    features = []
    for line in match.group(1).strip().splitlines():
        line = line.strip()
        if line.startswith("- "):
            # Strip markdown bold and leading dash
            clean = re.sub(r"\*\*(.*?)\*\*:?", r"\1:", line[2:]).strip()
            if clean:
                features.append(clean)
    return features or ["Zero-dependency runtime guardrails for AI agents"]


def read_whats_new() -> list[str]:
    """Get recent changes from git log since last tag, or last 5 commits."""
    try:
        # Try to get commits since last tag
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        if tag.returncode == 0 and tag.stdout.strip():
            ref = tag.stdout.strip()
            result = subprocess.run(
                ["git", "log", f"{ref}..HEAD", "--oneline", "--no-merges", "-10"],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
        else:
            result = subprocess.run(
                ["git", "log", "--oneline", "--no-merges", "-5"],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )

        if result.returncode == 0 and result.stdout.strip():
            lines = []
            for line in result.stdout.strip().splitlines():
                # Strip commit hash
                msg = line.split(" ", 1)[1] if " " in line else line
                if msg and not msg.startswith("Merge"):
                    lines.append(msg)
            return lines[:5] if lines else ["Latest release"]
    except Exception:
        pass
    return ["Latest release"]


def build_snippets() -> dict[str, str]:
    """Build code snippets from current API surface.

    These snippets use the real public API. If the API changes,
    tests/test_scout.py will catch the breakage.
    """
    return {
        "loop_guard": (
            "from agentguard import LoopGuard\n"
            "\n"
            "guard = LoopGuard(max_repeats=3)\n"
            'guard.check(tool_name="search", tool_args={"query": "..."})\n'
            "# raises LoopDetected after 3 identical calls"
        ),
        "budget_guard": (
            "from agentguard import BudgetGuard\n"
            "\n"
            "guard = BudgetGuard(max_cost_usd=5.00)  # stop at $5\n"
            "guard.consume(cost_usd=0.12)  # track per-call cost\n"
            "# raises BudgetExceeded when over budget"
        ),
        "langchain": (
            "from agentguard.integrations.langchain import AgentGuardCallbackHandler\n"
            "from agentguard import LoopGuard, BudgetGuard\n"
            "\n"
            "handler = AgentGuardCallbackHandler(\n"
            "    loop_guard=LoopGuard(max_repeats=3),\n"
            "    budget_guard=BudgetGuard(max_cost_usd=5.00),\n"
            ")\n"
            "llm = ChatOpenAI(callbacks=[handler])  # auto-tracks cost per call"
        ),
    }


def main() -> None:
    version, pkg_name = read_version()
    features = read_features()
    whats_new = read_whats_new()
    snippets = build_snippets()

    context = {
        "version": version,
        "package": pkg_name,
        "install_cmd": f"pip install {pkg_name}",
        "install_langchain_cmd": f"pip install {pkg_name}[langchain]",
        "repo_url": "https://github.com/bmdhodl/agent47",
        "pypi_url": f"https://pypi.org/project/{pkg_name}/",
        "features": features,
        "features_bullets": "\n".join(f"- {f}" for f in features),
        "snippets": snippets,
        "whats_new": whats_new,
        "whats_new_bullets": "\n".join(f"- {w}" for w in whats_new),
    }

    out_path = os.path.join(REPO_ROOT, "docs", "outreach", "scout_context.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(context, f, indent=2)
        f.write("\n")

    print(f"Wrote {out_path} (v{version}, {len(features)} features)")


if __name__ == "__main__":
    main()
