"""Offline proof: an uninstrumented child outlives an ``agentguard run`` parent.

The controller releases the child only after the guarded parent has exited.
The child writes two simulated dispatches to a local file. No provider, socket,
credentials, or billable request is used. This characterizes an unsupported
boundary; it does not add process supervision to AgentGuard.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SCRIPT = Path(__file__).resolve()


def wait_for(path: Path, scratch: Path, timeout: float = 12) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if (scratch / "stop").exists() or time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out or cancelled waiting for {path.name}")
        time.sleep(0.02)


def child(scratch: Path) -> None:
    # No AgentGuard initialization: this is a separate Python interpreter.
    (scratch / "ready").write_text(str(os.getpid()), encoding="utf-8")
    wait_for(scratch / "release", scratch)
    with (scratch / "mock-calls.jsonl").open("w", encoding="utf-8") as calls:
        for number in range(2):
            calls.write(json.dumps({"mock_dispatch": number + 1}) + "\n")
    (scratch / "done").touch()


def parent(scratch: Path) -> None:
    # Inherit the controller's stdout/stderr pipes. Their EOF lets the
    # controller wait for the child too, without adding an AgentGuard supervisor.
    subprocess.Popen(
        [sys.executable, str(SCRIPT), "--child", str(scratch)],
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=HIDDEN,
    )
    wait_for(scratch / "ready", scratch)
    # Return without joining the child, as a background task launcher would.


def reproduce(scratch_parent: Path | None) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="agentguard-child-", dir=scratch_parent) as directory:
        scratch = Path(directory)
        command = [
            sys.executable, "-m", "agentguard", "run", "--budget-usd", "0.01",
            str(SCRIPT), "--parent", str(scratch),
        ]
        process = subprocess.Popen(
            command, cwd=scratch, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", creationflags=HIDDEN,
        )
        try:
            # wait() observes the guarded parent's exit independently of the
            # inherited output pipes, which stay open while the child runs.
            parent_exit = process.wait(timeout=15)
            if parent_exit != 0:
                raise RuntimeError(f"Guarded parent exited {parent_exit}")
            if not (scratch / "ready").exists() or (scratch / "done").exists():
                raise RuntimeError("Child did not wait for the parent to exit")
            (scratch / "release").touch()
            wait_for(scratch / "done", scratch)
            stdout, stderr = process.communicate(timeout=15)
            if not (scratch / "done").exists():
                raise RuntimeError(f"Child did not complete: {stdout}\n{stderr}")
            count = len((scratch / "mock-calls.jsonl").read_text(encoding="utf-8").splitlines())
            return {
                "guarded_parent_exit_code": parent_exit,
                "mock_calls_after_parent_exit": count,
                "child_completed": True,
                "network_calls": 0,
                "coverage": "unsupported",
            }
        finally:
            # Only this example's child can see these markers. It also has a
            # bounded wait of its own if the controller is interrupted.
            (scratch / "stop").touch()
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=15)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--parent", type=Path)
    modes.add_argument("--child", type=Path)
    parser.add_argument("--scratch-parent", type=Path)
    args = parser.parse_args()
    if args.child is not None:
        child(args.child)
    elif args.parent is not None:
        parent(args.parent)
    else:
        print(json.dumps(reproduce(args.scratch_parent), sort_keys=True))


if __name__ == "__main__":
    main()
