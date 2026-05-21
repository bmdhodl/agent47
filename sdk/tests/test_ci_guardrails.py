from pathlib import Path


def test_actionlint_workflow_is_wired() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "actionlint.yml"

    assert workflow.exists(), "agent47 must run actionlint before workflow changes merge"
    text = workflow.read_text(encoding="utf-8")
    assert "rhysd/actionlint" in text
    assert ".github/workflows" in text
