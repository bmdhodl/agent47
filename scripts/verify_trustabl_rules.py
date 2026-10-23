"""Refuse a Trustabl scan unless its configured rules tag matches inspection."""
import argparse
import json
import os
import re
import sys
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API = "https://api.github.com/repos/trustabl/agent-reliability-rules/"


def read_object(endpoint: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(API + endpoint, headers=headers), timeout=20) as response:
        return json.loads(response.read())["object"]


def checked_object(endpoint: str) -> tuple[str, str]:
    obj = read_object(endpoint)
    kind, sha = obj["type"], obj["sha"]
    if kind not in {"tag", "commit"} or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("GitHub returned an invalid tag/commit object")
    return kind, sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--expected", required=True)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected):
        parser.error("--expected must be a full lowercase commit SHA")
    try:
        kind, resolved = checked_object(f"git/ref/tags/{quote(args.ref, safe='')}")
        if kind == "tag":
            kind, resolved = checked_object(f"git/tags/{resolved}")
        if kind != "commit":
            raise ValueError("Annotated rules tag does not point to a commit")
    except (URLError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Could not verify rules tag {args.ref}: {error}", file=sys.stderr)
        return 1
    if resolved != args.expected:
        print(f"Rules tag {args.ref}: expected {args.expected}, resolved {resolved}", file=sys.stderr)
        return 1
    print(f"Rules tag {args.ref} matches inspected commit {resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
