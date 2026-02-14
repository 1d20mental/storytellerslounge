#!/usr/bin/env bash
set -euo pipefail

# Recovery helper that works even when downtime_bot/ is missing from current checkout.
# Run from repository root: /opt/storytellerslounge
# Required env vars:
#   REPO_URL=git@github.com:ORG/REPO.git (or https://github.com/ORG/REPO.git)
#   REF=branch-or-tag (defaults to main)

REPO_URL=${REPO_URL:-}
REF=${REF:-main}
TARGET_DIR=${TARGET_DIR:-$(pwd)}
WORK_DIR=${WORK_DIR:-/tmp/storytellerslounge-downtime-sync}

if [ -z "$REPO_URL" ]; then
  echo "ERROR: set REPO_URL (example: git@github.com:ORG/REPO.git)" >&2
  exit 1
fi

if [ ! -d "$TARGET_DIR/.git" ]; then
  echo "ERROR: TARGET_DIR is not a git checkout: $TARGET_DIR" >&2
  exit 1
fi

rm -rf "$WORK_DIR"
git clone --depth 1 --branch "$REF" "$REPO_URL" "$WORK_DIR"

if [ ! -d "$WORK_DIR/downtime_bot" ]; then
  echo "ERROR: ref '$REF' in '$REPO_URL' does not contain downtime_bot/" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/data/allowed_content"
rm -rf "$TARGET_DIR/downtime_bot"
cp -a "$WORK_DIR/downtime_bot" "$TARGET_DIR/downtime_bot"

if [ -f "$WORK_DIR/data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json" ]; then
  cp -a "$WORK_DIR/data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json" \
    "$TARGET_DIR/data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json"
fi

echo "Recovered downtime_bot/ into $TARGET_DIR from $REPO_URL@$REF"
echo "Next: ls -la downtime_bot && bash downtime_bot/scripts/bootstrap_hetzner.sh"
