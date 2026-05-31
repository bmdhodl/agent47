"""Validate SDK release metadata and doc markers stay in sync."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import generate_pypi_readme

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NPM_COMMAND = "npm.cmd" if sys.platform == "win32" else "npm"
PYPROJECT_PATH = Path("sdk/pyproject.toml")
CHANGELOG_PATH = Path("CHANGELOG.md")
MCP_PACKAGE_PATH = Path("mcp-server/package.json")
MCP_SERVER_JSON_PATH = Path("mcp-server/server.json")
MCP_RUNTIME_INDEX_PATH = Path("mcp-server/src/index.ts")
RELEASE_MARKERS = (
    ("AGENTS.md", r"release candidate: v(?P<version>\d+\.\d+\.\d+)"),
    ("AGENTS.md", r"current SDK release candidate is (?P<version>\d+\.\d+\.\d+)"),
    ("AGENTS.md", r"current release candidate is (?P<version>\d+\.\d+\.\d+)"),
    ("CLAUDE.md", r"Current release candidate: v(?P<version>\d+\.\d+\.\d+)"),
    ("CLAUDE.md", r"release candidate is (?P<version>\d+\.\d+\.\d+)"),
    (".claude/agents/sdk-dev.md", r"Current SDK release candidate: `v(?P<version>\d+\.\d+\.\d+)`"),
)
RELEASE_TAG_PREFIX = "refs/tags/"


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


def _release_tag_from_ref(ref: Optional[str]) -> Optional[str]:
    if not ref:
        return None
    if ref.startswith(RELEASE_TAG_PREFIX):
        tag = ref.removeprefix(RELEASE_TAG_PREFIX)
        if re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            return tag
        return None
    if re.fullmatch(r"v\d+\.\d+\.\d+", ref):
        return ref
    return None


def check_release_tag(version: str, ref: Optional[str] = None) -> List[Finding]:
    release_ref = ref if ref is not None else os.environ.get("GITHUB_REF")
    tag = _release_tag_from_ref(release_ref)
    if tag is None:
        return []

    expected = f"v{version}"
    if tag == expected:
        return []

    return [
        Finding(
            check="release-tag",
            path="GITHUB_REF",
            message=(
                f"Tag {tag} does not match sdk/pyproject.toml version {version}. "
                f"Expected release tag {expected}; delete the stale tag and retag "
                "the release commit before publishing."
            ),
        )
    ]


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


def get_npm_command() -> str:
    """Return the npm executable used for optional registry verification."""
    return os.environ.get("AGENTGUARD_NPM_COMMAND") or DEFAULT_NPM_COMMAND


def check_mcp_npm_package(repo_root: Path, npm_command: Optional[str] = None) -> List[Finding]:
    """Optionally verify the repo MCP package version is published on npm."""
    command = npm_command or get_npm_command()
    package_path = repo_root / MCP_PACKAGE_PATH
    if not package_path.exists():
        return []

    package = json.loads(package_path.read_text(encoding="utf-8"))
    package_name = package.get("name")
    package_version = package.get("version")
    if not package_name or not package_version:
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message="Expected MCP package name and version before checking npm.",
            )
        ]

    try:
        exact_result = subprocess.run(
            [command, "view", f"{package_name}@{package_version}", "version"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message=(
                    f"Could not run {command} for npm verification. "
                    f"Install npm or set AGENTGUARD_NPM_COMMAND. {exc}"
                ),
            )
        ]
    if exact_result.returncode != 0:
        detail = (exact_result.stderr or exact_result.stdout).strip()
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message=f"Expected {package_name}@{package_version} to be published on npm. {detail}",
            )
        ]

    try:
        latest_result = subprocess.run(
            [command, "view", package_name, "version"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message=(
                    f"Could not run {command} for npm verification. "
                    f"Install npm or set AGENTGUARD_NPM_COMMAND. {exc}"
                ),
            )
        ]
    if latest_result.returncode != 0:
        detail = (latest_result.stderr or latest_result.stdout).strip()
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message=f"Could not read latest npm version for {package_name}. {detail}",
            )
        ]

    latest_version = latest_result.stdout.strip()
    if latest_version != package_version:
        return [
            Finding(
                check="mcp-npm",
                path=str(MCP_PACKAGE_PATH),
                message=f"Expected npm latest {package_version}, found {latest_version}.",
            )
        ]
    return []


def collect_findings(repo_root: Path, check_mcp_npm: bool = False) -> List[Finding]:
    version = load_version(repo_root)
    findings: List[Finding] = []
    findings.extend(check_release_tag(version))
    findings.extend(check_changelog(repo_root, version))
    findings.extend(check_pypi_readme(repo_root))
    findings.extend(check_release_markers(repo_root, version))
    findings.extend(check_mcp_metadata(repo_root))
    if check_mcp_npm:
        findings.extend(check_mcp_npm_package(repo_root))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument(
        "--check-mcp-npm",
        action="store_true",
        help="Also verify the MCP package version is published as npm latest. Uses network.",
    )
    args = parser.parse_args(argv)

    findings = collect_findings(REPO_ROOT, check_mcp_npm=args.check_mcp_npm)
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
