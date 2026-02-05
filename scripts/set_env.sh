#!/usr/bin/env bash
set -euo pipefail

trap 'echo "Error: deploy script failed. See output above."' ERR

if ! command -v vercel >/dev/null 2>&1; then
  echo "Vercel CLI not found. Install with: npm i -g vercel"
  exit 1
fi

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "Set VERCEL_TOKEN to avoid deprecated login. Example:"
  echo "  export VERCEL_TOKEN=your_token"
  exit 1
fi

if [ -z "${RESEND_API_KEY:-}" ]; then
  echo "Enter Resend API key (input hidden):"
  read -r -s RESEND_API_KEY
  printf "\n"
fi

if [ -z "${RESEND_API_KEY:-}" ]; then
  echo "No key provided. Aborting."
  exit 1
fi

if [ ! -d ".vercel" ]; then
  echo "Linking project..."
  vercel link --token "$VERCEL_TOKEN"
fi

echo "Setting RESEND_API_KEY in Vercel [production]..."
vercel env rm RESEND_API_KEY production --yes --token "$VERCEL_TOKEN" >/dev/null 2>&1 || true
printf "RESEND_API_KEY=%s\n" "$RESEND_API_KEY" | vercel env add RESEND_API_KEY production --token "$VERCEL_TOKEN"

echo "Deploying to production..."
vercel --prod --token "$VERCEL_TOKEN"

echo "Done."
