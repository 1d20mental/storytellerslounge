#!/usr/bin/env bash
set -euo pipefail

# Push the current branch and open clear next steps so downtime_bot/ exists on GitHub.
# Usage:
#   bash downtime_bot/scripts/publish_downtime_to_github.sh
# Optional:
#   REMOTE=origin TARGET_BRANCH=main bash ...

REMOTE=${REMOTE:-origin}
TARGET_BRANCH=${TARGET_BRANCH:-main}
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not inside a git repository" >&2
  exit 1
fi

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "ERROR: git remote '$REMOTE' is not configured." >&2
  echo "Set it, then rerun:" >&2
  echo "  git remote add $REMOTE git@github.com:<ORG>/<REPO>.git" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: working tree is dirty. Commit/stash changes first." >&2
  exit 1
fi

echo "Pushing branch '$CURRENT_BRANCH' to '$REMOTE'..."
git push -u "$REMOTE" "$CURRENT_BRANCH"

echo
echo "Next: create and merge PR so '$TARGET_BRANCH' contains downtime_bot/."
echo "Suggested commands:"
echo "  git checkout $TARGET_BRANCH"
echo "  git pull"
echo "  git merge --no-ff $CURRENT_BRANCH"
echo "  git push $REMOTE $TARGET_BRANCH"
echo
echo "Verify remote branch has downtime_bot/:"
echo "  git ls-tree -d --name-only $REMOTE/$TARGET_BRANCH | grep -x downtime_bot"
