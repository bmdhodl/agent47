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
    assert "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6" in text
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
