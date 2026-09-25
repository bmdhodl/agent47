"""Measure that the PR patch stays under the Claude review 200k cap."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = 200_000
ATTR_LINE = ".showwork/snapshots/*.json text eol=lf -diff"
METHODS = (b"def reserve(", b"def commit(", b"def cancel(", b"def mark_unresolved(")


def main() -> int:
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    if ATTR_LINE not in attrs:
        raise SystemExit("missing snapshot -diff rule in .gitattributes")

    probe = subprocess.run(
        [
            "git",
            "check-attr",
            "diff",
            "text",
            "eol",
            "--",
            ".showwork/snapshots/ag-03-reservation-contract.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if "diff: unset" not in probe.stdout or "text: set" not in probe.stdout:
        raise SystemExit(f"unexpected attrs:\n{probe.stdout}")

    patch = subprocess.run(
        ["git", "diff", "origin/main"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    size = len(patch)
    missing = [m.decode() for m in METHODS if m not in patch]
    if size >= CAP:
        raise SystemExit(f"patch {size} bytes exceeds cap {CAP}")
    if missing:
        raise SystemExit(f"patch missing methods: {missing}")

    out = ROOT / "proof" / "ag-03-reservation-contract" / "review-diff-size.txt"
    out.write_text(
        (
            f"worktree_diff_bytes={size}\n"
            f"cap_bytes={CAP}\n"
            "reserve_visible=true\n"
            "commit_visible=true\n"
            "cancel_visible=true\n"
            "mark_unresolved_visible=true\n"
            "note=Measured after .gitattributes -diff on "
            ".showwork/snapshots/*.json. Snapshot file bytes unchanged.\n"
        ),
        encoding="ascii",
    )
    snapshot_hunks = [
        hunk
        for hunk in re.split(rb"(?=^diff --git )", patch, flags=re.M)
        if b".showwork/snapshots/" in hunk.split(b"\n", 1)[0]
    ]
    for hunk in snapshot_hunks:
        if b"Binary files" not in hunk:
            raise SystemExit("snapshot hunk still has a text body")
    print("review_diff_ok")
    print(f"worktree_diff_bytes={size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
