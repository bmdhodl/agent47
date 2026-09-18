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
    assert "mcp>=1.23,<2" in manifest_text
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


def test_proof_snapshots_are_not_live_pip_requirements() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    matches = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "proof").rglob("*")
        if path.is_file() and "requirements" in path.name.lower() and path.suffix == ".txt"
    )
    assert matches == [], matches
