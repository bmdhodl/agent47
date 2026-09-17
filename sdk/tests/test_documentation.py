import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("docs_checker", ROOT / "scripts/check_docs.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_documentation_links():
    errors = []
    for name in checker.DOCS:
        path = ROOT / name
        if path.exists():
            errors.extend(checker.check_file(path, repository="agent47"))
    assert errors == []


def test_readme_python_floor_matches_package_metadata():
    import re
    metadata = (ROOT / "sdk/pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python = ">=([0-9.]+)"', metadata).group(1)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"Python {floor} or newer" in readme


@pytest.mark.parametrize("link", ["[missing](gone.md)", "[heading](other.md#gone)",
                                  "![](other.md)"])
def test_broken_documentation_is_rejected(tmp_path, link):
    (tmp_path / "other.md").write_text("# Existing\n", encoding="utf-8")
    path = tmp_path / "README.md"
    path.write_text("# Test\n" + link, encoding="utf-8")
    assert checker.check_file(path, root=tmp_path)


def test_valid_heading_and_code_example_link_are_accepted(tmp_path):
    (tmp_path / "other.md").write_text("# Existing\n", encoding="utf-8")
    path = tmp_path / "README.md"
    path.write_text("# Test\n[heading](other.md#existing)\n"
                    "```python\n# [example](not-a-real-link)\n```\n", encoding="utf-8")
    assert checker.check_file(path, root=tmp_path) == []

@pytest.mark.parametrize("link", ['[guide](missing.md "Guide")',
                                  "![image](missing.png 'Diagram')"])
def test_link_titles_do_not_hide_missing_targets(tmp_path, link):
    # REGRESSION: a Markdown title made the whole link invisible to the checker.
    path = tmp_path / "README.md"
    path.write_text("# Test\n" + link, encoding="utf-8")
    assert checker.check_file(path, root=tmp_path)


@pytest.mark.parametrize("fence", ["~~~~", "````", "~~~", "   ```"])
def test_all_fenced_examples_are_ignored(tmp_path, fence):
    # REGRESSION: valid alternative fences exposed example links to validation.
    path = tmp_path / "README.md"
    path.write_text("# Test\n" + fence + "text\n[example](missing.md)\n"
                    + fence + "\n", encoding="utf-8")
    assert checker.check_file(path, root=tmp_path) == []


def test_missing_entry_points_fail(tmp_path):
    # REGRESSION: deleting a curated document silently skipped its checks.
    assert checker.check_documents(tmp_path, "agent47")


def test_current_entry_points_exist_and_pass():
    assert checker.check_documents(ROOT, "agent47") == []


def test_readme_budget_example_stops_before_third_call(capsys):
    import re
    # REGRESSION: profile docs used a nonexistent import; execute the real example.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    code = re.findall(r"```python\n(.*?)```", readme, re.S)[0]
    namespace = {}
    exec(compile(code, "README.md", "exec"), namespace)
    assert namespace["completed"] == 2
    assert capsys.readouterr().out.strip() == "Stopped before call 3"


def test_getting_started_trace_example(tmp_path, monkeypatch):
    import json
    import re
    monkeypatch.chdir(tmp_path)
    doc = (ROOT / "docs/guides/getting-started.md").read_text(encoding="utf-8")
    code = re.findall(r"```python\n(.*?)```", doc, re.S)[0]
    exec(compile(code, "getting-started.md", "exec"), {})
    events = [json.loads(line) for line in
              (tmp_path / ".agentguard/traces.jsonl").read_text().splitlines()]
    assert any(event.get("name") == "tool.result" for event in events)
