#!/usr/bin/env bash
set -euo pipefail

# Example usage:
#   LIVE_HOST=user@server LIVE_PATH=/opt/www.hackerspace-drenthe.nl ./scripts/deploy_with_delete_example.sh
#
# This deploy style prevents stale files after renames (e.g. 001.foo -> 044.foo)
# by syncing with --delete before rebuilding/restarting containers.

: "${LIVE_HOST:?Set LIVE_HOST, e.g. user@server}"
: "${LIVE_PATH:?Set LIVE_PATH on live host}"

rsync -az --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  ./ "${LIVE_HOST}:${LIVE_PATH}/"

ssh "${LIVE_HOST}" "
  set -euo pipefail
  cd '${LIVE_PATH}'
  docker compose build --pull grav
  docker compose up -d --force-recreate grav
  docker compose exec -T grav php /config/www/bin/grav clear-cache || true
"

python3 scripts/check_live_news_duplicates.py "https://hackerspace-drenthe.nl"
