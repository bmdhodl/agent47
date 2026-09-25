import re
from pathlib import Path


def _contains_ordered_lines(lines: list[str], expected: list[str]) -> bool:
    if not expected:
        return True

    cursor = 0
    for line in lines:
        if line == expected[cursor]:
            cursor += 1
            if cursor == len(expected):
                return True
    return False


def test_actionlint_workflow_is_wired() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "actionlint.yml"

    assert workflow.exists(), "agent47 must run actionlint before workflow changes merge"
    text = workflow.read_text(encoding="utf-8")
    assert '      - ".github/workflows/**"' in text
    assert "pull_request:" in text
    assert "push:" in text
    assert "github.com/rhysd/actionlint/cmd/actionlint@v1.7.12" in text
    assert "actionlint -shellcheck=" in text
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0" in text
    assert "actions/setup-go@924ae3a1cded613372ab5595356fb5720e22ba16 # v6.5.0" in text


def test_release_content_waits_for_published_github_release() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "release-content.yml"

    assert workflow.exists(), "release announcements must stay under workflow guardrails"
    text = workflow.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert _contains_ordered_lines(
        lines,
        [
            "on:",
            "  release:",
            "    types:",
            "      - published",
        ],
    )
    assert _contains_ordered_lines(
        lines,
        [
            "  workflow_dispatch:",
            "    inputs:",
            "      tag:",
            "        required: true",
        ],
    )
    assert all(not line.startswith("  push:") for line in lines)
    assert "github.event.inputs.tag || github.event.release.tag_name" in text
    assert 'gh release list --exclude-drafts --exclude-pre-releases --json tagName' in text
    assert 'PREV_TAG="$(gh release list' in text
    assert 'git tag --sort=-creatordate' not in text


def test_publish_workflow_release_steps_are_post_publish_rerunnable() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "publish.yml"

    assert workflow.exists(), "PyPI publishing must stay under workflow guardrails"
    text = workflow.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert _contains_ordered_lines(
        lines,
        [
            "      - name: Verify tag matches sdk/pyproject.toml version",
            "        run: |",
            '          TAG_VERSION="${GITHUB_REF#refs/tags/v}"',
            '          PKG_VERSION="$(python -c \'import tomllib; print(tomllib.load(open("sdk/pyproject.toml","rb"))["project"]["version"])\')"',
            '          if [ "$TAG_VERSION" != "$PKG_VERSION" ]; then',
            '            echo "Tag $TAG_VERSION does not match sdk/pyproject.toml version $PKG_VERSION" >&2',
            "            exit 1",
            "          fi",
        ],
    )
    assert _contains_ordered_lines(
        lines,
        [
            "  github-release:",
            "    runs-on: ubuntu-latest",
            "    needs: publish",
            "    env:",
            "      GH_REPO: ${{ github.repository }}",
        ],
    )
    assert _contains_ordered_lines(
        lines,
        [
            "    permissions:",
            "      contents: write",
            "      actions: write",
        ],
    )

    normalized_text = text.replace("\r\n", "\n")
    publish_job = normalized_text.split("\n  github-release:", maxsplit=1)[0]
    release_job = normalized_text.split("\n  github-release:", maxsplit=1)[1]
    assert "Create GitHub Release" not in publish_job
    assert 'gh release view "$TAG"' in release_job
    assert 'gh release create "$TAG"' in release_job
    assert "--notes-start-tag" in release_job
    assert 'PREV_RELEASE_TAG="$(gh release list' in release_job
    assert "gh workflow run release-content.yml" in release_job
    assert '-f tag="$TAG"' in release_job
    assert "gh release upload" not in release_job


def test_ci_mcp_budget_job_installs_hashed_deps_without_editable_pip() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "ci.yml"
    lockfile = repo_root / ".github" / "requirements" / "mcp-budget.txt"
    manifest = repo_root / ".github" / "requirements" / "mcp-budget.in"

    text = workflow.read_text(encoding="utf-8")
    assert "python -m pip install --require-hashes -r .github/requirements/ci-tools.txt" in text
    assert "python -m pip install --require-hashes -r .github/requirements/mcp-budget.txt" in text
    assert "python -m pip install -e ./agentguard-mcp" not in text
    assert "working-directory: agentguard-mcp" in text
    assert "PYTHONPATH: ." in text
    assert lockfile.exists(), "CI must pin agentguard-mcp deps with a hashed lockfile"
    lock_text = lockfile.read_text(encoding="utf-8")
    assert "--hash=sha256:" in lock_text
    assert lock_text.count("mcp==") >= 1
    manifest_text = manifest.read_text(encoding="utf-8")
    # agentguard-mcp is imported via PYTHONPATH, so pip never checks its
    # declared runtime deps. The lock manifest must carry them verbatim.
    pyproject = (repo_root / "agentguard-mcp" / "pyproject.toml").read_text(encoding="utf-8")
    deps_block = re.search(r"^dependencies = \[(.*?)^\]", pyproject, re.M | re.S)
    assert deps_block is not None
    declared = re.findall(r'"([^"]+)"', deps_block.group(1))
    assert declared
    for dep in declared:
        assert dep in manifest_text, f"{dep} missing from mcp-budget.in"
    assert "pytest==" not in manifest_text
    assert "ruff==" not in manifest_text


def test_claude_review_checks_out_github_sha_not_pull_request_sha() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "claude-review.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "ref: ${{ github.sha }}" in text
    assert "ref: ${{ github.event.pull_request.base.sha }}" not in text
    assert "ref: ${{ github.event.pull_request.head.sha }}" not in text
    assert "pull_request_target:" in text
    assert "application/vnd.github.diff" in text
    assert "gh pr diff" not in text
    assert "--allow-escape-sequences" not in text
    assert "2>/tmp/review.err" in text


def test_github_actions_under_dot_github_are_pinned() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    unpinned = []
    for path in sorted((repo_root / ".github").rglob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            uses = stripped.split("uses:", 1)[1].strip()
            if uses.startswith("./") or uses.startswith(".github/"):
                continue
            _action, _, ref = uses.partition("@")
            comment_sha = ""
            if " #" in ref:
                ref, _, comment_sha = ref.partition(" #")
                ref = ref.strip()
            if len(ref) != 40 or any(ch not in "0123456789abcdef" for ch in ref.lower()):
                unpinned.append(f"{path.relative_to(repo_root)}:{lineno}:{uses}")
            elif not comment_sha.strip():
                unpinned.append(f"{path.relative_to(repo_root)}:{lineno}:missing version comment")
    assert unpinned == [], unpinned


def test_code_scanning_proof_logs_do_not_contain_ansi() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proof_dir = repo_root / "proof" / "code-scanning-20260918"
    offenders = []
    for path in sorted(proof_dir.rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\x1b[" in data:
            offenders.append(path.relative_to(repo_root).as_posix())
    assert offenders == []


def test_proof_snapshots_are_not_live_pip_requirements() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    matches = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "proof").rglob("*")
        if path.is_file() and "requirements" in path.name.lower() and path.suffix == ".txt"
    )
    assert matches == [], matches


def test_compat_floor_lock_matches_sdk_extra_floors() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    pyproject = (repo_root / "sdk" / "pyproject.toml").read_text(encoding="utf-8")
    extras = re.search(r"^\[project\.optional-dependencies\](.*?)^\[", pyproject, re.M | re.S)
    assert extras is not None
    floors = {
        name: version
        for name, version in re.findall(r'"([A-Za-z0-9_.-]+)>=([^",]+)"', extras.group(1))
        if name != "crewai"
    }
    assert floors
    manifest = (repo_root / ".github" / "requirements" / "compat-floor.in").read_text(encoding="utf-8")
    for name, version in floors.items():
        assert f"{name}=={version}" in manifest, f"compat-floor.in must pin {name}=={version}"
    for lock in ("compat-floor.txt", "compat-latest.txt"):
        text = (repo_root / ".github" / "requirements" / lock).read_text(encoding="utf-8")
        assert "--hash=sha256:" in text
        assert "crewai==" not in text


def test_ci_compat_job_fails_instead_of_skipping() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    text = (repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    job = text.split("  compat:\n", 1)[1]
    assert 'AGENTGUARD_REQUIRE_REAL_DEPS: "1"' in job
    assert "lock: [floor, latest]" in job
    assert "--require-hashes -r .github/requirements/compat-${{ matrix.lock }}.txt" in job
