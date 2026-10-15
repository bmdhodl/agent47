"""The versioned design reference and generated tokens must agree."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("shared_design_contract", ROOT / "scripts/check_design_contract.py")
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def test_reference_and_generated_values_agree():
    assert contract.verify(ROOT) == []


@pytest.mark.parametrize("filename", ["DESIGN.md", "design-tokens.json", "design-tokens.css"])
def test_modified_artifact_fails(tmp_path, filename):
    for name in ("DESIGN.md", "design-tokens.json", "design-tokens.css"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    target = tmp_path / filename
    target.write_text(target.read_text(encoding="utf-8").replace("#FF8200", "#FE8200"), encoding="utf-8")
    assert contract.verify(tmp_path)


def test_missing_artifacts_fail(tmp_path):
    assert contract.verify(tmp_path)


def test_regression_json_edit_cannot_keep_old_hashes(tmp_path):
    for name in ("DESIGN.md", "design-tokens.json", "design-tokens.css"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    path = tmp_path / "design-tokens.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["tokens"]["rounded"]["md"] = "24px"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert "CSS values differ from the generated token data" in contract.verify(tmp_path)
