"""Drop bulk generated files from a PR diff, then cap it for the reviewer.

Hash-pinned lockfiles and showwork snapshots sort early in the API diff and can
fill the 200k budget before any code. The reviewer still sees which files were
omitted. Reads the diff from stdin and writes the filtered diff to stdout.
"""
import fnmatch
import re
import sys

LIMIT = 200_000
OMIT = (
    ".github/requirements/*.txt",
    ".showwork/snapshots/*.json",
    "*package-lock.json",
)
HEADER = re.compile(rb"^diff --git a/(\S+) b/", re.M)


def filter_diff(diff: bytes, limit: int = LIMIT) -> bytes:
    starts = [match.start() for match in HEADER.finditer(diff)]
    if not starts:
        return diff[:limit]
    kept = [diff[: starts[0]]]
    omitted = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(diff)
        path = HEADER.match(diff, start).group(1).decode("utf-8", "replace")
        if any(fnmatch.fnmatch(path, pattern) for pattern in OMIT):
            omitted.append(path)
        else:
            kept.append(diff[start:end])
    note = b""
    if omitted:
        note = ("Generated files changed but omitted from this diff: " + ", ".join(omitted) + "\n\n").encode()
    return (note + b"".join(kept))[:limit]


if __name__ == "__main__":
    sys.stdout.buffer.write(filter_diff(sys.stdin.buffer.read()))
