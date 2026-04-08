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
MCP_PACKAGE_PATH = Path("mcp-server/package.json")
MCP_SERVER_JSON_PATH = Path("mcp-server/server.json")
MCP_RUNTIME_INDEX_PATH = Path("mcp-server/src/index.ts")
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


def check_mcp_metadata(repo_root: Path) -> List[Finding]:
    package_path = repo_root / MCP_PACKAGE_PATH
    server_json_path = repo_root / MCP_SERVER_JSON_PATH
    runtime_index_path = repo_root / MCP_RUNTIME_INDEX_PATH
    if not package_path.exists() or not server_json_path.exists():
        return []

    package = json.loads(package_path.read_text(encoding="utf-8"))
    server_json = json.loads(server_json_path.read_text(encoding="utf-8"))

    package_version = package.get("version")
    server_version = server_json.get("version")
    package_entries = server_json.get("packages") or []
    published_version = package_entries[0].get("version") if package_entries else None

    findings: List[Finding] = []
    if package_version != server_version:
        findings.append(
            Finding(
                check="mcp-metadata",
                path=str(MCP_SERVER_JSON_PATH),
                message=(
                    f"Expected MCP server.json version {package_version}, found {server_version}."
                ),
            )
        )
    if package_version != published_version:
        findings.append(
            Finding(
                check="mcp-metadata",
                path=str(MCP_SERVER_JSON_PATH),
                message=(
                    "Expected MCP package entry version "
                    f"{package_version}, found {published_version}."
                ),
            )
        )
    if runtime_index_path.exists():
        runtime_text = runtime_index_path.read_text(encoding="utf-8")
        match = re.search(r'version:\s*"(?P<version>\d+\.\d+\.\d+)"', runtime_text)
        runtime_version = match.group("version") if match else None
        if runtime_version != package_version:
            findings.append(
                Finding(
                    check="mcp-metadata",
                    path=str(MCP_RUNTIME_INDEX_PATH),
                    message=(
                        f"Expected MCP runtime version {package_version}, found {runtime_version}."
                    ),
                )
            )
    return findings


def collect_findings(repo_root: Path) -> List[Finding]:
    version = load_version(repo_root)
    findings: List[Finding] = []
    findings.extend(check_changelog(repo_root, version))
    findings.extend(check_pypi_readme(repo_root))
    findings.extend(check_release_markers(repo_root, version))
    findings.extend(check_mcp_metadata(repo_root))
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
