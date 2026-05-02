from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_pypi_readme.py"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_pypi_readme", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_pypi_readme_includes_current_release_notes() -> None:
    module = _load_generator_module()

    version = module._load_version(REPO_ROOT)
    content = module.build_pypi_readme(REPO_ROOT)
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = module.extract_release_notes(changelog, version)

    assert f"## Latest Release Notes ({version})" in content
    assert release_notes in content
    assert f"https://github.com/bmdhodl/agent47/blob/v{version}/LICENSE" in content
    assert f"https://github.com/bmdhodl/agent47/blob/v{version}/CHANGELOG.md" in content
    assert (
        f"https://colab.research.google.com/github/bmdhodl/agent47/blob/v{version}/examples/quickstart.ipynb"
        in content
    )


def test_generated_pypi_readme_links_unreleased_guide_to_main() -> None:
    module = _load_generator_module()

    content = module.build_pypi_readme(REPO_ROOT)

    assert (
        "https://github.com/bmdhodl/agent47/blob/main/docs/guides/decision-tracing.md"
        in content
    )


def test_generated_pypi_readme_links_unreleased_sample_incident_to_main() -> None:
    module = _load_generator_module()

    content = module.build_pypi_readme(REPO_ROOT)

    assert (
        "https://github.com/bmdhodl/agent47/blob/main/docs/examples/coding-agent-review-loop-incident.md"
        in content
    )


def test_committed_pypi_readme_is_in_sync() -> None:
    module = _load_generator_module()

    expected = module.build_pypi_readme(REPO_ROOT)
    actual = (REPO_ROOT / "sdk" / "PYPI_README.md").read_text(encoding="utf-8")

    assert actual == expected
