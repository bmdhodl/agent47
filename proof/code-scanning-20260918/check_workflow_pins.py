"""Fail if CI still uses an unhashed editable agentguard-mcp install."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
REVIEW = (ROOT / ".github" / "workflows" / "claude-review.yml").read_text(encoding="utf-8")

assert "python -m pip install --require-hashes -r .github/requirements/mcp-budget.txt" in CI
assert "python -m pip install -e ./agentguard-mcp" not in CI
assert "ref: ${{ github.sha }}" in REVIEW
assert "ref: ${{ github.event.pull_request.base.sha }}" not in REVIEW
assert "--allow-escape-sequences" in REVIEW
print("passed")
