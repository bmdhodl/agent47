#!/usr/bin/env bash
# Build the 2.0.0 wheel and sdist like publish.yml, then run the first-use
# commands from a clean Python 3.11 venv in an empty directory.
# Usage: bash proof/v2.0.0/clean_install.sh <work-dir>   (run from the repo root)
# Windows only (Git Bash): it uses the py launcher and venv Scripts/python.exe.
case "$OSTYPE" in
    msys*|cygwin*) ;;
    *) echo "clean_install.sh targets Windows Git Bash (py launcher, Scripts/python.exe); OSTYPE is $OSTYPE" >&2; exit 1 ;;
esac
# No set -e: step logs each exit code, and the last step must fail. Setup
# commands outside step stop the script instead, so a failed cd cannot run
# the first-use steps from the repo root.
set -u
work="$1"
repo="$(pwd)"
rm -rf "$work"
mkdir -p "$work/dist" "$work/run" || exit 1

step() { echo "\$ $*"; "$@"; echo "exit=$?"; }

SOURCE_DATE_EPOCH=315532800 step python -m build ./sdk --outdir "$work/dist"
(cd "$work/dist" && step sha256sum agentguard47-2.0.0-py3-none-any.whl agentguard47-2.0.0.tar.gz)

step py -3.11 -m venv "$work/venv311"
py311="$work/venv311/Scripts/python.exe"
step "$py311" -I -m pip --isolated install --quiet --no-deps --no-index "$work/dist/agentguard47-2.0.0-py3-none-any.whl"
step "$py311" -I -m pip show agentguard47

cd "$work/run" || exit 1
step "$py311" -I -m agentguard --version
step "$py311" -I -m agentguard doctor
step "$py311" -I -m agentguard demo
step "$py311" -I -m agentguard report agentguard_demo_traces.jsonl
step "$py311" -I -m agentguard receipt agentguard_demo_traces.jsonl
step "$py311" -I -m agentguard quickstart --framework raw --write
step "$py311" -I agentguard_raw_quickstart.py
step "$py311" -I -m agentguard report .agentguard/traces.jsonl
step "$py311" -I -m agentguard hook claude-code --help
step "$py311" -I -m agentguard run --help
cd "$repo" || exit 1

# Python 3.10 must refuse the 2.0.0 wheel (requires-python >=3.11).
step py -3.10 -m venv "$work/venv310"
step "$work/venv310/Scripts/python.exe" -I -m pip --isolated install --quiet --no-deps --no-index "$work/dist/agentguard47-2.0.0-py3-none-any.whl"
