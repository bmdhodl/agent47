"""Claude review drops bulk generated files before the diff budget."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("filter_diff", ROOT / ".github/claude-review/filter_diff.py")
filter_diff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filter_diff)


def _section(path: str, body: str) -> bytes:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n{body}\n".encode()


def test_lockfiles_and_snapshots_are_named_but_not_sent():
    diff = (
        _section(".github/requirements/compat-latest.txt", "+x==1 \\\n+    --hash=sha256:" + "a" * 5000)
        + _section(".showwork/snapshots/s.json", "+{}" * 5000)
        + _section("mcp-server/package-lock.json", "+{}")
        + _section(".github/workflows/ci.yml", "+  compat:")
    )
    out = filter_diff.filter_diff(diff)
    assert out.startswith(b"Generated files changed but omitted from this diff: ")
    for path in (b".github/requirements/compat-latest.txt", b".showwork/snapshots/s.json", b"mcp-server/package-lock.json"):
        assert path in out.split(b"\n", 1)[0]
        assert b"diff --git a/" + path not in out
    assert b"diff --git a/.github/workflows/ci.yml" in out
    assert b"+  compat:" in out


def test_code_after_a_huge_lockfile_survives_the_cap():
    # REGRESSION: PR #777's lockfiles filled the 200k cap and hid ci.yml.
    diff = _section(".github/requirements/compat-floor.txt", "+" + "h" * 300_000) + _section("sdk/agentguard/cli.py", "+fix")
    out = filter_diff.filter_diff(diff)
    assert b"sdk/agentguard/cli.py" in out
    assert len(out) < 1000


def test_cap_still_applies_to_kept_files():
    out = filter_diff.filter_diff(_section("sdk/big.py", "+" + "x" * 300_000), limit=200_000)
    assert len(out) == 200_000


def test_diff_without_sections_is_capped_unchanged():
    assert filter_diff.filter_diff(b"not a diff", limit=3) == b"not"
