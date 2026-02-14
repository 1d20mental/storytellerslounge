#!/usr/bin/env bash
set -euo pipefail

# Pull downtime_bot files directly from GitHub into an existing server checkout.
# Supports public repos via clone URL; private repos work with SSH clone URLs if keys are configured.

REPO_URL=${REPO_URL:-}
REF=${REF:-main}
TARGET_DIR=${TARGET_DIR:-/opt/storytellerslounge}
WORK_DIR=${WORK_DIR:-/tmp/storytellerslounge-downtime-sync}

if [ -z "$REPO_URL" ]; then
  echo "ERROR: set REPO_URL, e.g. REPO_URL=git@github.com:ORG/REPO.git" >&2
  exit 1
fi

rm -rf "$WORK_DIR"
git clone --depth 1 --branch "$REF" "$REPO_URL" "$WORK_DIR"

if [ ! -d "$WORK_DIR/downtime_bot" ]; then
  echo "ERROR: ref '$REF' in $REPO_URL does not contain downtime_bot/" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/data/allowed_content"
rm -rf "$TARGET_DIR/downtime_bot"
cp -a "$WORK_DIR/downtime_bot" "$TARGET_DIR/downtime_bot"
cp -a "$WORK_DIR/data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json" \
  "$TARGET_DIR/data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json"
cp -a "$WORK_DIR/requirements.txt" "$TARGET_DIR/requirements.txt"

echo "Synced downtime_bot subtree into $TARGET_DIR from $REPO_URL@$REF"
