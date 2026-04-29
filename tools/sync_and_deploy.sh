#!/usr/bin/env bash
# Run gallery sync, then commit + push if anything changed.
# Triggered by the launchd watcher when files land in site/public/assets/website_dino_images/.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/tools/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/sync.log"

{
  echo
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

  # Debounce: give a multi-file drop or a slow copy time to finish.
  sleep 6

  if ! python3 tools/sync_gallery.py; then
    echo "sync_gallery.py failed; aborting deploy."
    exit 1
  fi

  WATCH_DIR="site/public/assets/website_dino_images"
  PRODUCTS="site/src/data/products.json"

  if [ -z "$(git status --porcelain "$PRODUCTS" "$WATCH_DIR")" ]; then
    echo "No changes detected — nothing to push."
    exit 0
  fi

  git add "$PRODUCTS" "$WATCH_DIR"

  ADDED=$(git diff --cached --name-only --diff-filter=A -- "$WATCH_DIR" | wc -l | tr -d ' ')
  REMOVED=$(git diff --cached --name-only --diff-filter=D -- "$WATCH_DIR" | wc -l | tr -d ' ')

  PARTS=()
  [ "$ADDED" -gt 0 ] && PARTS+=("+$ADDED added")
  [ "$REMOVED" -gt 0 ] && PARTS+=("-$REMOVED removed")
  [ ${#PARTS[@]} -eq 0 ] && PARTS+=("metadata refresh")

  IFS=", "
  MSG="Auto-sync gallery: ${PARTS[*]}"
  unset IFS

  if ! git commit -m "$MSG"; then
    echo "git commit failed."
    exit 1
  fi

  if ! git push origin HEAD:main; then
    echo "git push failed — commit was made locally."
    exit 1
  fi

  echo "Pushed: $MSG"
} >> "$LOG" 2>&1
