"""Check the portable design artifacts without a generator or runtime dependency."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def properties(tokens: dict, prefix: str = "bmd") -> dict[str, str]:
    result = {}
    for key, value in tokens.items():
        name = prefix + "-" + re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key).lower()
        if isinstance(value, dict):
            result.update(properties(value, name))
        else:
            result[name] = str(value)
    return result


def verify(root: Path) -> list[str]:
    try:
        markdown = read_text(root / "DESIGN.md")
        css = read_text(root / "design-tokens.css")
        data = json.loads(read_text(root / "design-tokens.json"))
        if not isinstance(data, dict) or not isinstance(data.get("tokens"), dict):
            return ["Generated design token data is missing"]
        errors = []
        for label, content, key in (("DESIGN.md", markdown, "source_sha256"),
                                    ("design-tokens.css", css, "css_sha256")):
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != data.get(key):
                errors.append(f"{label} differs from its generated hash")
        version = re.search(r'^design_version:[ \t]*[\'"]?([0-9]+\.[0-9]+\.[0-9]+)', markdown, re.MULTILINE)
        if not version or version.group(1) != data.get("design_version"):
            errors.append("Design versions differ")
        declarations = re.findall(r"^  --([a-z0-9-]+): (.*);$", css, re.MULTILINE)
        if len(declarations) != len(dict(declarations)) or dict(declarations) != properties(data["tokens"]):
            errors.append("CSS values differ from the generated token data")
        return errors
    except (OSError, ValueError, TypeError) as exc:
        return [f"Cannot verify design artifacts: {exc}"]


if __name__ == "__main__":
    findings = verify(Path(__file__).resolve().parents[1])
    print("\n".join(findings) if findings else "design contract: current (visual review is separate)")
    raise SystemExit(2 if findings else 0)
