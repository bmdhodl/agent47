#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if ! command -v vercel >/dev/null 2>&1; then
  echo "Vercel CLI not found. Install with: npm i -g vercel"
  exit 1
fi

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "Set VERCEL_TOKEN to run end-to-end tests."
  exit 1
fi

if [ -z "${RESEND_API_KEY:-}" ]; then
  echo "Set RESEND_API_KEY to run end-to-end tests."
  exit 1
fi

if [ -z "${RESEND_TO_EMAIL:-}" ]; then
  echo "Set RESEND_TO_EMAIL to run end-to-end tests."
  exit 1
fi

if [ ! -d ".vercel" ]; then
  vercel link --token "$VERCEL_TOKEN"
fi

# Start vercel dev in the background
vercel dev --token "$VERCEL_TOKEN" >/tmp/agentguard_vercel_dev.log 2>&1 &
DEV_PID=$!

cleanup() {
  kill "$DEV_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Wait for dev server to be ready
for i in {1..20}; do
  if curl -s http://localhost:3000 >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -s http://localhost:3000 >/dev/null 2>&1; then
  echo "Vercel dev server did not start. Check /tmp/agentguard_vercel_dev.log"
  exit 1
fi

# Open the local page for visual verification
if command -v open >/dev/null 2>&1; then
  open http://localhost:3000
fi

# Capture a screenshot for each run
if command -v screencapture >/dev/null 2>&1; then
  sleep 2
  TS=$(date +"%Y%m%d_%H%M%S")
  SCREENSHOT_PATH="$ROOT_DIR/site_screenshots"
  mkdir -p "$SCREENSHOT_PATH"
  screencapture "$SCREENSHOT_PATH/agentguard_${TS}.png"
  echo "Saved screenshot: $SCREENSHOT_PATH/agentguard_${TS}.png"
fi

# Send a real request through the form endpoint
RESP=$(curl -s -X POST http://localhost:3000/api/lead \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$RESEND_TO_EMAIL\",\"source\":\"e2e\"}")

echo "Response: $RESP"

if ! echo "$RESP" | grep -q '"ok":true'; then
  echo "E2E test failed."
  exit 1
fi

echo "E2E test passed."
