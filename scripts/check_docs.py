"""Check curated documentation links without network access or dependencies.

Checks inline Markdown links, headings, image alt text, and local CI badges.
Historical reports are outside this entry-point check.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("README.md", "docs/README.md", "llms.txt", "docs/guides/getting-started.md")
LINK = re.compile(r"""(!?)\[([^\]\n]*)\]\(([^\s)]+)(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?\s*\)""")


def strip_fences(text):
    lines = []
    fence = None
    for line in text.splitlines():
        if fence is not None:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if opening:
            fence = opening.group(1)
        else:
            lines.append(line)
    return "\n".join(lines)


def headings(text):
    counts = {}
    result = set()
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def check_file(path, root=ROOT, repository=None):
    errors = []
    text = strip_fences(path.read_text(encoding="utf-8"))
    if not text.startswith("# "):
        errors.append(f"{path.name}: missing descriptive H1")
    for image, label, target in LINK.findall(text):
        if image and not label.strip():
            errors.append(f"{path.name}: image has no alt text")
        url = urlsplit(target.strip("<>"))
        if url.scheme or url.netloc:
            prefix = f"/bmdhodl/{repository}/" if repository else None
            if url.netloc == "github.com" and prefix and url.path.startswith(prefix):
                tail = url.path[len(prefix):]
                if tail.startswith(("blob/main/", "tree/main/")):
                    target_path = root / unquote(tail.split("/", 2)[2])
                elif tail.startswith("actions/workflows/"):
                    workflow = tail.split("/")[2]
                    target_path = root / ".github/workflows" / workflow
                else:
                    continue
            else:
                continue
        else:
            target_path = path.parent / unquote(url.path) if url.path else path
        if not target_path.exists():
            errors.append(f"{path.name}: missing link target {target}")
        elif url.fragment and target_path.is_file() and target_path.suffix == ".md":
            anchors = headings(strip_fences(target_path.read_text(encoding="utf-8")))
            if unquote(url.fragment) not in anchors:
                errors.append(f"{path.name}: missing heading {target}")
    return errors


def check_documents(root, repository):
    errors = []
    for name in DOCS:
        path = root / name
        if not path.is_file():
            errors.append(f"Missing documentation entry point: {name}")
        else:
            errors.extend(check_file(path, root=root, repository=repository))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    errors = check_documents(ROOT, args.repository)
    for error in errors:
        print(error)
    if not errors:
        print("Documentation links and image alt text passed")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
