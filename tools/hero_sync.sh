#!/usr/bin/env bash
# Hero reel drop handler — fires when an .mp4 lands in (or leaves) the hero
# folder. The hero auto-reads every clip in this folder at build time, so all
# this needs to do is commit + push; Vercel rebuilds and the clip joins the loop.
#
# Triggered by: com.jurassinkart.hero-sync launchd agent
# Watches: site/public/assets/hero/
# Logs: tools/logs/hero_sync.log

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/tools/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/hero_sync.log"

HERO_DIR="site/public/assets/hero"

{
  echo
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') hero-sync ==="

  # Debounce + wait for large video copies to finish: only proceed once the
  # folder's total byte size stops changing across two checks.
  sleep 5
  prev=""
  for _ in $(seq 1 20); do
    cur=$(find "$HERO_DIR" -type f -print0 2>/dev/null | xargs -0 stat -f '%z' 2>/dev/null | awk '{s+=$1} END {print s+0}')
    if [ "$cur" = "$prev" ]; then break; fi
    prev="$cur"
    sleep 3
  done

  if [ -z "$(git status --porcelain "$HERO_DIR")" ]; then
    echo "No changes — nothing to push."
    exit 0
  fi

  git add "$HERO_DIR"

  ADDED=$(git diff --cached --name-only --diff-filter=A -- "$HERO_DIR" | wc -l | tr -d ' ')
  REMOVED=$(git diff --cached --name-only --diff-filter=D -- "$HERO_DIR" | wc -l | tr -d ' ')

  PARTS=()
  [ "$ADDED" -gt 0 ] && PARTS+=("+$ADDED added")
  [ "$REMOVED" -gt 0 ] && PARTS+=("-$REMOVED removed")
  [ ${#PARTS[@]} -eq 0 ] && PARTS+=("refresh")

  IFS=", "
  MSG="Auto-sync hero reel: ${PARTS[*]}"
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
