#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

./set_env.sh

echo "Fetching deployment URL..."
DEPLOY_URL=$(vercel ls --meta --token "${VERCEL_TOKEN:-}" 2>/dev/null | awk 'NR==1 {print $2}')

if [ -z "$DEPLOY_URL" ]; then
  echo "Could not determine deployment URL. Check your Vercel dashboard."
  exit 1
fi

if [[ "$DEPLOY_URL" != http* ]]; then
  DEPLOY_URL="https://$DEPLOY_URL"
fi

echo "Opening $DEPLOY_URL"
open "$DEPLOY_URL"
