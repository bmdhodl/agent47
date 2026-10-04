from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci_tools_requirements_guard.py"
SPEC = importlib.util.spec_from_file_location("ci_tools_requirements_guard", SCRIPT_PATH)
assert SPEC is not None
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def metadata_with_python(specifier: str) -> dict:
    return {
        "info": {"requires_python": specifier},
        "urls": [{"requires_python": specifier, "yanked": False}],
    }


def _load_with_packaging_error(monkeypatch, error):
    import builtins
    import runpy

    original_import = builtins.__import__

    def import_package(name, *args, **kwargs):
        if name.startswith("packaging."):
            raise error
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_package)
    return runpy.run_path(str(SCRIPT_PATH))


def test_missing_packaging_keeps_stdlib_floor_validation(tmp_path, monkeypatch) -> None:
    fallback = _load_with_packaging_error(monkeypatch, ImportError("packaging absent"))
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("build==1.5.0\n", encoding="utf-8")
    findings = fallback["find_incompatible_pins"](
        requirements, (3, 11),
        metadata_lookup=lambda _name, _version: metadata_with_python(">=3.12"),
    )
    assert [finding.pin.name for finding in findings] == ["build"]


def test_packaging_runtime_error_is_not_swallowed(monkeypatch) -> None:
    """REGRESSION: a broken installed dependency must not activate the fallback."""
    try:
        _load_with_packaging_error(monkeypatch, RuntimeError("broken packaging import"))
    except RuntimeError as error:
        assert str(error) == "broken packaging import"
    else:
        raise AssertionError("Unexpected import failures must propagate")


def test_rejects_direct_pin_above_ci_python_floor(tmp_path: Path) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("build==1.5.0\n", encoding="utf-8")

    incompatible = guard.find_incompatible_pins(
        requirements,
        (3, 9),
        metadata_lookup=lambda _name, _version: metadata_with_python(">=3.10"),
    )

    assert [item.pin.name for item in incompatible] == ["build"]


def test_accepts_direct_pin_matching_ci_python_floor(tmp_path: Path) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("build==1.4.4\n", encoding="utf-8")

    incompatible = guard.find_incompatible_pins(
        requirements,
        (3, 9),
        metadata_lookup=lambda _name, _version: metadata_with_python(">=3.9"),
    )

    assert incompatible == []


def test_ci_tool_manifest_pins_python_floor_transitives() -> None:
    pin_names = {pin.name for pin in guard.read_direct_pins(guard.DEFAULT_REQUIREMENTS)}

    assert {"importlib-metadata", "zipp"}.issubset(pin_names)


def test_rejects_non_exact_direct_pins(tmp_path: Path) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("build>=1.4\n", encoding="utf-8")

    try:
        guard.read_direct_pins(requirements)
    except ValueError as exc:
        assert "expected an exact direct pin" in str(exc)
    else:
        raise AssertionError("non-exact CI tool pins must fail")


def test_skips_pin_when_environment_marker_excludes_python_floor(tmp_path: Path) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text('future-tool==2.0.0 ; python_version >= "3.10"\n', encoding="utf-8")

    incompatible = guard.find_incompatible_pins(
        requirements,
        (3, 9),
        metadata_lookup=lambda _name, _version: metadata_with_python(">=3.10"),
    )

    assert incompatible == []


def test_validates_pin_when_environment_marker_includes_python_floor(tmp_path: Path) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text('build==1.5.0 ; python_version >= "3.9"\n', encoding="utf-8")

    incompatible = guard.find_incompatible_pins(
        requirements,
        (3, 9),
        metadata_lookup=lambda _name, _version: metadata_with_python(">=3.10"),
    )

    assert [item.pin.name for item in incompatible] == ["build"]


def test_main_reports_value_errors_without_traceback(tmp_path: Path, capsys) -> None:
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("build==1.4.4\n", encoding="utf-8")

    result = guard.main(["--requirements", str(requirements), "--min-python", "three-nine"])

    captured = capsys.readouterr()
    assert result == 1
    assert "ci-tools requirements guard failed:" in captured.err
    assert "Traceback" not in captured.err


def test_default_floor_accepts_pytest9_but_rejects_python312_only_tools(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """REGRESSION: the supported SDK floor must accept pytest 9 without an override."""
    requirements = tmp_path / "ci-tools.in"
    requirements.write_text("pytest==9.0.3\n", encoding="utf-8")
    find = guard.find_incompatible_pins
    specifier = ">=3.10"
    monkeypatch.setattr(
        guard,
        "find_incompatible_pins",
        lambda path, version: find(
            path, version, metadata_lookup=lambda _name, _version: metadata_with_python(specifier)
        ),
    )

    assert guard.main(["--requirements", str(requirements)]) == 0
    assert "support Python 3.11" in capsys.readouterr().out

    specifier = ">=3.12"
    assert guard.main(["--requirements", str(requirements)]) == 1
    assert "Requires-Python >=3.12" in capsys.readouterr().err


def test_sdk_metadata_ci_matrix_and_tool_guard_share_the_supported_floor() -> None:
    """REGRESSION: installing tools on a retired interpreter breaks the required checks."""
    import re

    root = SCRIPT_PATH.parents[1]
    metadata = (root / "sdk" / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'^requires-python = ">=(\d+)\.(\d+)"$', metadata, re.MULTILINE)
    assert floor is not None
    assert tuple(map(int, floor.groups())) == guard.DEFAULT_MIN_PYTHON == (3, 11)
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert 'python-version: ["3.11", "3.12"]' in workflow
    assert '"Programming Language :: Python :: 3.9"' not in metadata
    assert '"Programming Language :: Python :: 3.10"' not in metadata
