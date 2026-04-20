#!/usr/bin/env bash
set -eu

TAG="vTEST"
PREV_TAG="vOLD"
MARKER="/tmp/agentguard_release_content_should_not_execute"
rm -f "$MARKER"

CHANGELOG="$(cat <<'CHANGELOG_EOF'
commit one contains `touch /tmp/agentguard_release_content_should_not_execute`
commit two contains $(touch /tmp/agentguard_release_content_should_not_execute)
commit three contains "quotes" and backslashes \ without breaking JSON variables
CHANGELOG_EOF
)"

BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

{
  printf '## AgentGuard %s Released\n\n' "$TAG"
  printf 'Install or upgrade:\n'
  printf '```bash\n'
  printf 'pip install --upgrade agentguard47\n'
  printf '```\n\n'
  printf '### What changed\n'
  printf '%s\n\n' "$CHANGELOG"
  printf -- '---\n'
  printf 'Full changelog: https://github.com/bmdhodl/agent47/compare/%s...%s\n\n' "$PREV_TAG" "$TAG"
  printf 'PyPI: https://pypi.org/project/agentguard47/\n'
} > "$BODY_FILE"

cat "$BODY_FILE"

if [ -e "$MARKER" ]; then
  echo "unsafe: changelog text executed"
  exit 1
fi

echo "safe: changelog text preserved as data"
