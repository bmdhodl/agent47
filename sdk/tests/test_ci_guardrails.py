from pathlib import Path


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

    text = workflow.read_text(encoding="utf-8")
    assert "release:" in text
    assert "published" in text
    assert "push:\n    tags:" not in text
    assert "github.event.release.tag_name" in text
