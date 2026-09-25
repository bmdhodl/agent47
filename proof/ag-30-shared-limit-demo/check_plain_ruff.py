"""Fail if the saved ruff proof still contains terminal color codes."""
from pathlib import Path


def main() -> None:
    data = Path("proof/ag-30-shared-limit-demo/ruff.txt").read_bytes()
    if b"\x1b" in data:
        raise SystemExit(1)
    if b"All checks passed!" not in data:
        raise SystemExit(1)
    print("plain_ruff")


if __name__ == "__main__":
    main()
