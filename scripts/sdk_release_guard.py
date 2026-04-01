"""Validate SDK release metadata and doc markers stay in sync."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence

import generate_pypi_readme

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = Path("sdk/pyproject.toml")
CHANGELOG_PATH = Path("CHANGELOG.md")
RELEASE_MARKERS = (
    ("AGENTS.md", r"latest shipped release: v(?P<version>\d+\.\d+\.\d+)"),
    ("AGENTS.md", r"latest shipped release is (?P<version>\d+\.\d+\.\d+)"),
    ("CLAUDE.md", r"latest shipped release: v(?P<version>\d+\.\d+\.\d+)"),
    ("CLAUDE.md", r"latest shipped release is (?P<version>\d+\.\d+\.\d+)"),
    (".claude/agents/sdk-dev.md", r"Latest shipped SDK release: `v(?P<version>\d+\.\d+\.\d+)`"),
)


@dataclass(frozen=True)
class Finding:
    check: str
    path: str
    message: str


def load_version(repo_root: Path) -> str:
    return generate_pypi_readme._load_version(repo_root)


def check_changelog(repo_root: Path, version: str) -> List[Finding]:
    changelog = (repo_root / CHANGELOG_PATH).read_text(encoding="utf-8")
    try:
        generate_pypi_readme.extract_release_notes(changelog, version)
    except ValueError as exc:
        return [
            Finding(
                check="changelog",
                path=str(CHANGELOG_PATH),
                message=str(exc),
            )
        ]
    return []


def check_pypi_readme(repo_root: Path) -> List[Finding]:
    try:
        exit_code = generate_pypi_readme.check_output(repo_root, generate_pypi_readme.OUTPUT_PATH)
    except ValueError as exc:
        return [
            Finding(
                check="pypi-readme",
                path=str(generate_pypi_readme.OUTPUT_PATH),
                message=str(exc),
            )
        ]
    if exit_code == 0:
        return []
    return [
        Finding(
            check="pypi-readme",
            path=str(generate_pypi_readme.OUTPUT_PATH),
            message="Generated PyPI README is out of date with README.md/CHANGELOG.md.",
        )
    ]


def check_release_markers(repo_root: Path, version: str) -> List[Finding]:
    findings: List[Finding] = []
    expected = version
    for relative_path, pattern in RELEASE_MARKERS:
        text = (repo_root / relative_path).read_text(encoding="utf-8")
        match = re.search(pattern, text)
        if match is None:
            findings.append(
                Finding(
                    check="release-markers",
                    path=relative_path,
                    message=f"Could not find expected release marker matching `{pattern}`.",
                )
            )
            continue
        actual = match.group("version")
        if actual != expected:
            findings.append(
                Finding(
                    check="release-markers",
                    path=relative_path,
                    message=f"Expected release marker {expected}, found {actual}.",
                )
            )
    return findings


def collect_findings(repo_root: Path) -> List[Finding]:
    version = load_version(repo_root)
    findings: List[Finding] = []
    findings.extend(check_changelog(repo_root, version))
    findings.extend(check_pypi_readme(repo_root))
    findings.extend(check_release_markers(repo_root, version))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    findings = collect_findings(REPO_ROOT)
    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    else:
        if findings:
            for finding in findings:
                print(f"[{finding.check}] {finding.path}: {finding.message}")
        else:
            print("Release guard passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
