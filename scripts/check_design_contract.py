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


TOKEN_GROUPS = ("colors", "typography", "spacing", "rounded", "motion", "components")


def source_tokens(markdown: str) -> dict:
    """Read the exported mapping/JSON-string token subset, never general YAML.

    Unsupported YAML fails closed; update the exporter and this reader together
    if the shared token grammar changes. Human-readable metadata is ignored.
    """
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", markdown, re.DOTALL)
    if not match:
        raise ValueError("DESIGN.md requires frontmatter")
    groups = {}
    stack = [(-2, groups)]
    active = False
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        entry = re.fullmatch(r"( *)([A-Za-z0-9_-]+):(?:[ \t]+(.*))?", line)
        if not entry:
            raise ValueError("Unsupported design frontmatter syntax")
        indent, key, raw = len(entry[1]), entry[2], entry[3]
        if indent == 0:
            active = key in TOKEN_GROUPS
            stack = [(-2, groups)]
        if not active:
            continue
        while indent <= stack[-1][0]:
            stack.pop()
        if indent != stack[-1][0] + 2 or key in stack[-1][1]:
            raise ValueError("Invalid token indentation or duplicate key")
        parent = stack[-1][1]
        if raw is None:
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            value = json.loads(raw)
            if not isinstance(value, str):
                raise ValueError("Design token values require JSON-quoted strings")
            parent[key] = value
    if set(groups) != set(TOKEN_GROUPS):
        raise ValueError("Missing source token groups")

    def resolve(value, references=()):
        if isinstance(value, dict):
            return {key: resolve(item, references) for key, item in value.items()}

        def replace(match):
            name = match[1]
            if name in references:
                raise ValueError("Cyclic source token reference")
            target = groups
            for key in name.split("."):
                if not isinstance(target, dict) or key not in target:
                    raise ValueError("Unknown source token reference")
                target = target[key]
            if isinstance(target, dict):
                raise ValueError("Source token reference must name a value")
            return resolve(target, references + (name,))

        return re.sub(r"\{([A-Za-z0-9_.-]+)\}", replace, value)

    return resolve(groups)


def verify(root: Path) -> list[str]:
    try:
        markdown = read_text(root / "DESIGN.md")
        css = read_text(root / "design-tokens.css")
        data = json.loads(read_text(root / "design-tokens.json"))
        if not isinstance(data, dict) or not isinstance(data.get("tokens"), dict):
            return ["Generated design token data is missing"]
        errors = []
        tokens = source_tokens(markdown)
        if tokens != data["tokens"]:
            errors.append("Source token values differ from generated data")
        for label, content, key in (("DESIGN.md", markdown, "source_sha256"),
                                    ("design-tokens.css", css, "css_sha256")):
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != data.get(key):
                errors.append(f"{label} differs from its generated hash")
        version = re.search(r'^design_version:[ \t]*[\'"]?([0-9]+\.[0-9]+\.[0-9]+)', markdown, re.MULTILINE)
        if not version or version.group(1) != data.get("design_version"):
            errors.append("Design versions differ")
        expected_css = (
            f"/* Generated from DESIGN.md v{data.get('design_version')}; do not edit.\n"
            f"   Source SHA256: {hashlib.sha256(markdown.encode('utf-8')).hexdigest()} */\n:root {{\n"
            + "".join(f"  --{name}: {value};\n" for name, value in properties(tokens).items())
            + "}\n"
        )
        if css != expected_css:
            errors.append("CSS differs from the generated source serialization")
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
