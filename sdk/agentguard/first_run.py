from __future__ import annotations

import sys
from typing import List, Optional, TextIO

LOCAL_TRACE_FILE = ".agentguard/traces.jsonl"
RAW_QUICKSTART_FILE = "agentguard_raw_quickstart.py"
RAW_QUICKSTART_COMMAND = "agentguard quickstart --framework raw --write"

GITHUB_REPO_URL = "https://github.com/bmdhodl/agent47"
STAR_CALL_TO_ACTION = (
    f"If AgentGuard saved you a runaway run, star it so others find it: {GITHUB_REPO_URL}"
)

# Paste-able proof badge. Every repo that adds it is a backlink and social proof,
# which is the cheapest network-effect surface the SDK has.
BADGE_MARKDOWN = (
    "[![Guarded by AgentGuard]"
    "(https://img.shields.io/badge/guarded%20by-AgentGuard-3b82f6)]"
    f"({GITHUB_REPO_URL})"
)
BADGE_RST = (
    ".. image:: https://img.shields.io/badge/guarded%20by-AgentGuard-3b82f6\n"
    f"   :target: {GITHUB_REPO_URL}\n"
    "   :alt: Guarded by AgentGuard"
)
BADGE_HTML = (
    f'<a href="{GITHUB_REPO_URL}">'
    '<img src="https://img.shields.io/badge/guarded%20by-AgentGuard-3b82f6" '
    'alt="Guarded by AgentGuard"></a>'
)


def local_proof_commands(*, include_demo: bool = False) -> List[str]:
    """Return the local-first proof path shown by first-run CLI commands."""
    commands = [
        RAW_QUICKSTART_COMMAND,
        f"python {RAW_QUICKSTART_FILE}",
        f"agentguard report {LOCAL_TRACE_FILE}",
    ]
    if include_demo:
        return ["agentguard demo", *commands]
    return commands


def render_welcome(stream: Optional[TextIO] = None, *, version: Optional[str] = None) -> None:
    """Print the friendly first-run welcome shown for a bare ``agentguard`` call.

    This is the most-typed command right after ``pip install`` and the first
    impression of the tool. Keep it short, local-first, and guide the user to a
    win in under a minute instead of dumping argparse help.
    """
    out = stream or sys.stdout
    header = "AgentGuard"
    if version:
        header = f"AgentGuard {version}"

    _print(out, header)
    _print(out, "Stop agents from looping, retrying forever, and burning budget.")
    _print(out, "Zero dependencies. Local-first. No API key needed.")
    _print(out, "")
    _print(out, "Try it in 60 seconds (all local, no network):")
    _print(out, "  agentguard doctor      verify the install and write a local trace")
    _print(out, "  agentguard demo        watch budget, loop, and retry guards stop a run")
    _print(out, f"  {RAW_QUICKSTART_COMMAND}   drop a starter into your repo")
    _print(out, "")
    _print(out, "More:")
    _print(out, "  agentguard --help      list every command")
    _print(out, "  agentguard badge       copy a README badge for your repo")
    _print(out, "")
    _print(out, "If 'agentguard' is not on PATH, prefix any command with 'python -m agentguard'.")
    _print(out, "")
    _print(out, STAR_CALL_TO_ACTION)


def render_badge(stream: Optional[TextIO] = None, *, fmt: str = "markdown") -> None:
    """Print a paste-able "Guarded by AgentGuard" badge for a repo README.

    The badge is the SDK's lowest-friction network-effect surface: a user who
    already trusts AgentGuard advertises it to every visitor of their repo.
    """
    out = stream or sys.stdout
    snippet = {
        "markdown": BADGE_MARKDOWN,
        "rst": BADGE_RST,
        "html": BADGE_HTML,
    }.get(fmt, BADGE_MARKDOWN)

    _print(out, "Guarded by AgentGuard badge:")
    _print(out, "")
    _print(out, snippet)
    _print(out, "")
    _print(out, f"Renders a blue badge that links back to {GITHUB_REPO_URL}")
    _print(out, "Add it to your README so other builders find AgentGuard.")


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")
