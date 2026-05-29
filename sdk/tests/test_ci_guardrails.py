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
    assert "actions/setup-go@40f1582b2485089dde7abd97c1529aa768e1baff # v5" in text


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


def test_publish_workflow_release_steps_are_post_publish_rerunnable() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "publish.yml"

    assert workflow.exists(), "PyPI publishing must stay under workflow guardrails"
    text = workflow.read_text(encoding="utf-8")
    lines = text.splitlines()
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
    assert "gh workflow run release-content.yml" in release_job
    assert '-f tag="$TAG"' in release_job
