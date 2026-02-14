#!/usr/bin/env bash
set -euo pipefail

# Create a deploy archive for servers where the git remote branch is missing downtime_bot/
REPO_DIR=${REPO_DIR:-$(pwd)}
OUTPUT_DIR=${OUTPUT_DIR:-$REPO_DIR/dist}
ARCHIVE_NAME=${ARCHIVE_NAME:-storytellerslounge-downtime_bot.tar.gz}

cd "$REPO_DIR"
mkdir -p "$OUTPUT_DIR"

if [ ! -d "downtime_bot" ]; then
  echo "ERROR: downtime_bot/ directory not found in $REPO_DIR" >&2
  exit 1
fi

if [ ! -f "data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json" ]; then
  echo "ERROR: required allowed content file is missing" >&2
  exit 1
fi

tar -czf "$OUTPUT_DIR/$ARCHIVE_NAME" \
  downtime_bot \
  data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json \
  requirements.txt

echo "Created deploy archive: $OUTPUT_DIR/$ARCHIVE_NAME"
