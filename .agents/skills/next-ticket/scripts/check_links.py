"""Fail unless every agent entry point reads the same next-ticket skill."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RELATIVE = (
    ".agents/skills/next-ticket/SKILL.md",
    ".claude/skills/next-ticket/SKILL.md",
    ".cursor/skills/next-ticket/SKILL.md",
    ".codex/skills/next-ticket/SKILL.md",
    ".github/skills/next-ticket/SKILL.md",
)
MARKER = "name: next-ticket"


def main() -> None:
    canonical = (ROOT / RELATIVE[0]).resolve()
    for rel in RELATIVE:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        if MARKER not in text:
            raise SystemExit(f"missing skill name: {rel}")
        if path.resolve() != canonical:
            raise SystemExit(f"not the same file: {rel}")
        print(f"ok {rel}")


if __name__ == "__main__":
    main()
