#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/storytellerslounge"
BRANCH="main"

cd "$REPO_ROOT"

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "Repository reset to origin/$BRANCH. Downtime bot files are now available under downtime_bot/."
