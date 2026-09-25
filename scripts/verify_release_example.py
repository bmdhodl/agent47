"""Verify the published wheel's offline example before release distribution."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from send_release_email import REPOSITORY, build_payload, get_json

EVENTS = {"guard.budget_exceeded", "guard.loop_detected", "guard.retry_limit_exceeded"}


def run(command, cwd):
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True,
                          timeout=120, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)


def validate_events(rows):
    names = {row.get("name") for row in rows}
    if not EVENTS.issubset(names):
        raise ValueError("Published demo did not produce all three guard stop events")


def verify_wheel(tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("A stable release tag is required")
    with tempfile.TemporaryDirectory(prefix="agentguard-release-") as folder:
        root = Path(folder)
        run([sys.executable, "-m", "venv", str(root / "venv")], root)
        python = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-I", "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
             "--index-url", "https://pypi.org/simple", "--only-binary=:all:", "--no-deps",
             f"agentguard47=={tag[1:]}"], root)
        # Exercise the public CLI, not an editable checkout. Refuse Python socket
        # connections while the offline demo runs. No provider credentials needed.
        probe = (
            "import importlib.metadata, runpy, socket, sys\n"
            f"assert importlib.metadata.version('agentguard47') == {tag[1:]!r}\n"
            "def offline(*args, **kwargs):\n    raise RuntimeError('Offline demo attempted network access')\n"
            "socket.socket.connect = offline\nsocket.create_connection = offline\n"
            "sys.argv = ['agentguard', 'demo', '--feedback']\n"
            "runpy.run_module('agentguard.cli', run_name='__main__')\n"
        )
        run([str(python), "-I", "-c", probe], root)
        rows = [json.loads(line) for line in (root / "agentguard_demo_traces.jsonl").read_text().splitlines() if line]
        validate_events(rows)
        run([str(python), "-I", "-m", "agentguard.cli", "report", "agentguard_demo_traces.jsonl"], root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        parser.error("A stable release tag is required")
    release = get_json(f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{args.tag}", os.environ.get("GH_TOKEN"))
    package = get_json(f"https://pypi.org/pypi/agentguard47/{args.tag[1:]}/json")
    build_payload(args.tag, release, package)
    verify_wheel(args.tag)
    result = (
        f"## Published AgentGuard {args.tag}: offline example passed\n\n"
        "Installed the exact PyPI wheel in a fresh environment. Budget, loop and "
        "retry stop events appeared; the report command completed. "
        "This is a simulated example, not proof of customer adoption or savings.\n\n"
        "[Run the example](https://github.com/bmdhodl/agent47/blob/main/docs/guides/try-release.md)\n"
    )
    print(result)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
            output.write(result)


if __name__ == "__main__":
    main()
