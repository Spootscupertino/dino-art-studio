#!/usr/bin/env bash
# Website drop handler — fires when files land in a category gallery folder.
# Pipeline: slug rename → sync products.json → git commit → push to Vercel.
#
# Triggered by: com.jurassinkart.web-sync launchd agent
# Watches: predators/ herbivores/ marine/ aerial/ flora_arthropods/
# Logs: tools/logs/web_sync.log

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/tools/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/web_sync.log"

{
  echo
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') web-sync ==="

  # Debounce: let multi-file drops finish before processing.
  sleep 6

  echo "--- Renaming to SEO slugs ---"
  python3 tools/slug_rename.py \
    site/src/assets/gallery/predators \
    site/src/assets/gallery/herbivores \
    site/src/assets/gallery/marine \
    site/src/assets/gallery/aerial \
    site/src/assets/gallery/flora_arthropods

  echo "--- Building products.json ---"
  if ! python3 tools/sync_gallery.py; then
    echo "sync_gallery.py failed — aborting deploy."
    exit 1
  fi

  WATCH_DIR="site/src/assets/gallery"
  PRODUCTS="site/src/data/products.json"

  if [ -z "$(git status --porcelain "$PRODUCTS" "$WATCH_DIR")" ]; then
    echo "No changes — nothing to push."
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
