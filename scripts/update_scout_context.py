#!/usr/bin/env python3
"""Generate scout_context.json from pyproject.toml and feature definitions.

Run from repo root:
    python scripts/update_scout_context.py

Outputs docs/outreach/scout_context.json with dynamic variables
that the scout workflow injects into comment templates.
"""
import json
import os
import sys

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    pyproject_path = os.path.join(REPO_ROOT, "sdk", "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    version = pyproject["project"]["version"]
    pkg_name = pyproject["project"]["name"]

    # Feature list — update this when shipping new features
    features = [
        "Cost tracking: dollar estimates per LLM call (OpenAI, Anthropic, Gemini, Mistral)",
        "Budget guards: `BudgetGuard(max_cost_usd=5.00)` stops agents before they blow your API budget",
        "Loop detection: catches repeated tool calls in a sliding window",
        "Replay: record and replay runs for deterministic testing",
        "LangChain integration: drop-in callback handler with auto cost + guard wiring",
        "Gantt trace viewer: timeline visualization in your browser",
        "Zero dependencies: pure Python stdlib, nothing to audit",
    ]

    # Code snippets for templates
    snippets = {
        "loop_guard": (
            "from agentguard import LoopGuard\n"
            "\n"
            "guard = LoopGuard(max_repeats=3)\n"
            "guard.check(tool_name=\"search\", tool_args={\"query\": \"...\"})\n"
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
        "quickstart": (
            "from agentguard import Tracer, BudgetGuard\n"
            "from agentguard.instrument import patch_openai\n"
            "\n"
            "tracer = Tracer(sink=JsonlFileSink(\"traces.jsonl\"))\n"
            "patch_openai(tracer)  # auto-tracks cost per call\n"
            "\n"
            "with tracer.trace(\"agent.run\") as span:\n"
            "    span.event(\"step\", data={\"thought\": \"search docs\"})"
        ),
    }

    # What's new — latest release highlights for the scout issue header
    whats_new = [
        f"v{version}: Cost tracking + dollar budget guards",
        "Estimated cost per LLM call (auto-detected from token usage)",
        "`BudgetGuard(max_cost_usd=N)` — dollar-based budget enforcement",
        "LangChain integration now auto-estimates cost and enforces budgets",
        "Hosted dashboard with costs page, savings banner",
    ]

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

    print(f"Wrote {out_path} (v{version})")


if __name__ == "__main__":
    main()
