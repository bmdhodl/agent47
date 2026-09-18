"""Fail if CI still uses an unhashed editable agentguard-mcp install."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
REVIEW = (ROOT / ".github" / "workflows" / "claude-review.yml").read_text(encoding="utf-8")

EVAL = (ROOT / ".github" / "actions" / "agentguard-eval" / "action.yml").read_text(
    encoding="utf-8"
)

assert "python -m pip install --require-hashes -r .github/requirements/mcp-budget.txt" in CI
assert "python -m pip install -e ./agentguard-mcp" not in CI
assert "ref: ${{ github.sha }}" in REVIEW
assert "ref: ${{ github.event.pull_request.base.sha }}" not in REVIEW
assert "application/vnd.github.diff" in REVIEW
assert "gh pr diff" not in REVIEW
assert "--allow-escape-sequences" not in REVIEW
assert "/tmp/review.err" in REVIEW
assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in EVAL
assert "actions/setup-python@v5" not in EVAL
print("passed")
