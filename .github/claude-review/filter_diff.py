"""Drop bulk generated files from a PR diff, then cap it for the reviewer.

Hash-pinned lockfiles and showwork snapshots sort early in the API diff and can
fill the 200k budget before any code. The reviewer still sees which files were
omitted. Reads the diff from stdin and writes the filtered diff to stdout.
"""
import fnmatch
import re
import sys

LIMIT = 200_000
NOTE_NAMES = 50
OMIT = (
    ".github/requirements/*.txt",
    ".showwork/snapshots/*.json",
    "*package-lock.json",
)
# Split on every file header, whatever its path looks like, so a path with
# spaces can never be swallowed into the previous section.
SECTION = re.compile(rb"^diff --git ", re.M)
PATH_LINE = re.compile(rb"^(?:--- a/|\+\+\+ b/|rename from |rename to )(.+?)\t?$", re.M)
HEADER_PATHS = re.compile(rb"^diff --git a/(\S+) b/(\S+)$", re.M)


def _paths(section: bytes) -> list:
    paths = [p.decode("utf-8", "replace") for p in PATH_LINE.findall(section)]
    header = HEADER_PATHS.match(section)
    if header:
        paths += [p.decode("utf-8", "replace") for p in header.groups()]
    return paths


def _generated(section: bytes) -> bool:
    # Omit only when every path on both sides of the change is generated.
    paths = _paths(section)
    return bool(paths) and all(any(fnmatch.fnmatch(p, pattern) for pattern in OMIT) for p in paths)


def filter_diff(diff: bytes, limit: int = LIMIT) -> bytes:
    starts = [match.start() for match in SECTION.finditer(diff)]
    if not starts:
        return diff[:limit]
    kept = [diff[: starts[0]]]
    omitted = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(diff)
        section = diff[start:end]
        if _generated(section):
            omitted.append(sorted(set(_paths(section)))[0])
        else:
            kept.append(section)
    note = b""
    if omitted:
        names = ", ".join(omitted[:NOTE_NAMES])
        if len(omitted) > NOTE_NAMES:
            names += f", and {len(omitted) - NOTE_NAMES} more"
        note = f"Generated files changed but omitted from this diff: {names}\n\n".encode()
    return (note + b"".join(kept))[:limit]


if __name__ == "__main__":
    sys.stdout.buffer.write(filter_diff(sys.stdin.buffer.read()))
