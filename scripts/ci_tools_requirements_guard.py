"""Validate CI-tool pins against the SDK's Python support floor."""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Optional

try:
    from packaging.markers import InvalidMarker, Marker
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
except Exception:  # pragma: no cover - fallback keeps the script stdlib-runnable.
    InvalidMarker = None
    Marker = None
    SpecifierSet = None
    Version = None


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIREMENTS = REPO_ROOT / ".github" / "requirements" / "ci-tools.in"
DEFAULT_MIN_PYTHON = (3, 9)
PIN_RE = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^;\s]+)(?:\s*;\s*(?P<marker>.+))?$")


@dataclasses.dataclass(frozen=True)
class DirectPin:
    name: str
    version: str
    line_number: int
    marker: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class IncompatiblePin:
    pin: DirectPin
    requires_python: tuple[str, ...]


def normalize_name(name: str) -> str:
    return name.replace("_", "-").lower()


def parse_python_version(value: str) -> tuple[int, int]:
    parts = value.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Expected Python version like 3.9, got {value!r}")
    return int(parts[0]), int(parts[1])


def read_direct_pins(path: Path) -> list[DirectPin]:
    pins: list[DirectPin] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_RE.match(line)
        if not match:
            raise ValueError(f"{path}:{line_number}: expected an exact direct pin like package==1.2.3")
        pins.append(
            DirectPin(
                name=normalize_name(match.group("name")),
                version=match.group("version"),
                line_number=line_number,
                marker=match.group("marker"),
            )
        )
    return pins


def _version_text(version: tuple[int, int]) -> str:
    return f"{version[0]}.{version[1]}"


def _parse_numeric_version(value: str) -> tuple[int, int, int]:
    numeric_parts = re.findall(r"\d+", value)
    if not numeric_parts:
        raise ValueError(f"Unsupported version in Requires-Python specifier: {value!r}")
    padded = [int(part) for part in numeric_parts[:3]]
    while len(padded) < 3:
        padded.append(0)
    return tuple(padded)  # type: ignore[return-value]


def _fallback_supports_python(specifier: str, python_version: tuple[int, int]) -> bool:
    candidate = (python_version[0], python_version[1], 0)
    for raw_part in specifier.split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = re.match(r"^(===|==|!=|<=|>=|<|>|~=)\s*([0-9][A-Za-z0-9.*+!_-]*)$", part)
        if not match:
            raise ValueError(f"Unsupported Requires-Python specifier: {specifier!r}")
        operator, version_text = match.groups()
        if operator == "~=":
            lower = _parse_numeric_version(version_text)
            components = [int(piece) for piece in re.findall(r"\d+", version_text)]
            upper = (components[0] + 1, 0, 0) if len(components) <= 2 else (components[0], components[1] + 1, 0)
            if not (candidate >= lower and candidate < upper):
                return False
            continue
        if "*" in version_text:
            prefix = tuple(int(piece) for piece in version_text.split("*", 1)[0].strip(".").split(".") if piece)
            matches = candidate[: len(prefix)] == prefix
            if operator == "==" and not matches:
                return False
            if operator == "!=" and matches:
                return False
            continue
        pinned = _parse_numeric_version(version_text)
        if operator in {"==", "==="} and candidate != pinned:
            return False
        if operator == "!=" and candidate == pinned:
            return False
        if operator == ">=" and candidate < pinned:
            return False
        if operator == ">" and candidate <= pinned:
            return False
        if operator == "<=" and candidate > pinned:
            return False
        if operator == "<" and candidate >= pinned:
            return False
    return True


def _fallback_marker_applies(marker: str, python_version: tuple[int, int]) -> bool:
    match = re.fullmatch(r"""python_version\s*(==|!=|<=|>=|<|>)\s*["']([0-9.]+)["']""", marker.strip())
    if not match:
        raise ValueError(f"Unsupported environment marker: {marker!r}")
    operator, version_text = match.groups()
    candidate = (python_version[0], python_version[1], 0)
    pinned = _parse_numeric_version(version_text)
    if operator == "==":
        return candidate == pinned
    if operator == "!=":
        return candidate != pinned
    if operator == ">=":
        return candidate >= pinned
    if operator == ">":
        return candidate > pinned
    if operator == "<=":
        return candidate <= pinned
    if operator == "<":
        return candidate < pinned
    raise ValueError(f"Unsupported environment marker: {marker!r}")


def marker_applies(marker: Optional[str], python_version: tuple[int, int]) -> bool:
    if not marker:
        return True
    environment = {"python_version": _version_text(python_version)}
    if Marker is not None:
        try:
            return Marker(marker).evaluate(environment=environment)
        except Exception as exc:
            if InvalidMarker is not None and isinstance(exc, InvalidMarker):
                raise ValueError(f"Unsupported environment marker: {marker!r}") from exc
            raise
    return _fallback_marker_applies(marker, python_version)


def supports_python(specifier: Optional[str], python_version: tuple[int, int]) -> bool:
    if not specifier:
        return True
    if SpecifierSet is not None and Version is not None:
        return Version(_version_text(python_version)) in SpecifierSet(specifier)
    return _fallback_supports_python(specifier, python_version)


def fetch_pypi_release_metadata(package: str, version: str) -> dict:
    package_url = urllib.parse.quote(package)
    version_url = urllib.parse.quote(version)
    url = f"https://pypi.org/pypi/{package_url}/{version_url}/json"
    request = urllib.request.Request(url, headers={"User-Agent": "agentguard-ci-tools-guard"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError(f"{package}=={version} does not exist on PyPI") from exc
        raise ValueError(f"Could not fetch PyPI metadata for {package}=={version} from {url}: {exc}") from exc
    except (TimeoutError, urllib.error.URLError) as exc:
        raise ValueError(f"Could not fetch PyPI metadata for {package}=={version} from {url}: {exc}") from exc


def release_requires_python(metadata: dict) -> tuple[str, ...]:
    info_specifier = (metadata.get("info") or {}).get("requires_python") or ""
    urls = [item for item in metadata.get("urls", []) if not item.get("yanked")]
    if not urls:
        return (info_specifier,)
    return tuple((item.get("requires_python") or info_specifier or "") for item in urls)


def find_incompatible_pins(
    requirements_path: Path,
    python_version: tuple[int, int],
    metadata_lookup: Callable[[str, str], dict] = fetch_pypi_release_metadata,
) -> list[IncompatiblePin]:
    incompatible: list[IncompatiblePin] = []
    for pin in read_direct_pins(requirements_path):
        if not marker_applies(pin.marker, python_version):
            continue
        metadata = metadata_lookup(pin.name, pin.version)
        specifiers = release_requires_python(metadata)
        if not any(supports_python(specifier, python_version) for specifier in specifiers):
            incompatible.append(IncompatiblePin(pin=pin, requires_python=specifiers))
    return incompatible


def format_incompatible(incompatible: Iterable[IncompatiblePin], python_version: tuple[int, int]) -> str:
    target = _version_text(python_version)
    lines = [f"CI tool pins must support Python {target}:"]
    for item in incompatible:
        specs = ", ".join(spec or "<unspecified>" for spec in item.requires_python)
        lines.append(
            f"- line {item.pin.line_number}: {item.pin.name}=={item.pin.version} "
            f"has Requires-Python {specs}"
        )
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--min-python", default=_version_text(DEFAULT_MIN_PYTHON))
    args = parser.parse_args(argv)

    try:
        python_version = parse_python_version(args.min_python)
        incompatible = find_incompatible_pins(args.requirements, python_version)
    except ValueError as exc:
        print(f"ci-tools requirements guard failed: {exc}", file=sys.stderr)
        return 1
    if incompatible:
        print(format_incompatible(incompatible, python_version), file=sys.stderr)
        return 1
    print(f"{args.requirements} direct pins support Python {_version_text(python_version)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
