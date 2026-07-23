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
