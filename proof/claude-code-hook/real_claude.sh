#!/usr/bin/env bash
# Reproduce: install the hook in a scratch project and drive real Claude Code.
# Usage: proof/claude-code-hook/real_claude.sh <scratch-dir> <python-with-agentguard>
set -euo pipefail
dir=$1; py=$2
rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"; git init -q
"$py" -m agentguard.cli hook claude-code --install --write --project-dir .
claude --version
echo "== loop: identical command four times"
claude -p "Use the Bash tool to run exactly this command: echo agentguard-sentinel . Run it four separate times, one call at a time, with the identical command each time, even if a call is refused. Then report verbatim any refusal messages you saw." \
  --model claude-haiku-4-5-20251001 --allowedTools Bash --max-turns 12 < /dev/null
echo "== retry: failing command with other calls between"
claude -p "Use the Bash tool for each step, one call at a time, in this exact order, even if a call fails or is refused: 1) ls /nonexistent-agentguard  2) echo one  3) ls /nonexistent-agentguard  4) echo two  5) ls /nonexistent-agentguard . Then report verbatim any refusal messages." \
  --model claude-haiku-4-5-20251001 --allowedTools Bash --max-turns 14 < /dev/null
echo "== receipt"
"$py" -m agentguard.cli receipt .agentguard/claude-code/trace.jsonl
