#!/usr/bin/env bash
# Printify drop handler — fires when files land in horizontal/ or vertical/.
# Pipeline: slug rename → web promote → site deploy → auto-log → Printify drafts.
# Printify publishing is scoped to the NEW winners web_promote just added, and
# always creates drafts only (never auto-pushes to Etsy).
#
# Triggered by: com.jurassinkart.printify-sync launchd agent
# Watches: horizontal/ vertical/
# Logs: tools/logs/printify_sync.log

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/tools/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/printify_sync.log"

{
  echo
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') printify-sync ==="

  # Debounce: let multi-file drops finish before processing.
  sleep 6

  echo "--- Renaming to SEO slugs ---"
  python3 tools/slug_rename.py \
    site/src/assets/gallery/horizontal \
    site/src/assets/gallery/vertical

  echo "--- Promoting to website gallery with SEO captions ---"
  WEB_OUT="$(python3 tools/web_promote.py \
    site/src/assets/gallery/horizontal \
    site/src/assets/gallery/vertical)"
  echo "$WEB_OUT"
  # Gallery-relative paths of the winners web_promote just added (scopes Printify).
  NEW_RELS="$(printf '%s\n' "$WEB_OUT" | awk -F'\t' '/^NEW_IMAGE/{print $2}')"

  echo "--- Rebuilding products.json + deploying to jurassinkart.com ---"
  python3 tools/sync_gallery.py

  PRODUCTS="site/src/data/products.json"
  WATCH_DIR="site/src/assets/gallery"
  if [ -n "$(git status --porcelain "$PRODUCTS" "$WATCH_DIR")" ]; then
    git add "$PRODUCTS" "$WATCH_DIR"
    git commit -m "Auto-promote 9+ winner: SEO slug + caption + website sync"
    git push origin HEAD:main
    echo "--- Deployed to jurassinkart.com ---"
  else
    echo "--- No website changes to deploy ---"
  fi

  echo "--- Auto-logging curated images to feedback loop ---"
  python3 feedback_agent.py --auto-log site/src/assets/gallery/horizontal
  python3 feedback_agent.py --auto-log site/src/assets/gallery/vertical

  echo "--- Printify: upscale + resize + create drafts (new winners only) ---"
  if [ -z "$NEW_RELS" ]; then
    echo "--- No new winners this run; skipping Printify ---"
  else
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      echo "  [printify] drafting $rel"
      python3 printify/printify_publisher.py \
        --image "site/src/assets/gallery/$rel" --live --draft 2>&1 || true
    done <<< "$NEW_RELS"
  fi

  echo "=== Done. Site live + Printify drafts ready for Etsy approval. ==="
} >> "$LOG" 2>&1
