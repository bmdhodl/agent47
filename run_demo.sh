#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/patrickhughes/Documents/New project"
SDK_DIR="$ROOT_DIR/sdk"
DEMO_PY="$SDK_DIR/examples/demo_agent.py"
TRACES="$SDK_DIR/examples/traces.jsonl"

python3 -m pip install -e "$SDK_DIR"
python3 "$DEMO_PY"
python3 -m agentguard.cli report "$TRACES"
