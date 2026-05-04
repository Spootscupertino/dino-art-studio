#!/usr/bin/env bash
# Printify drop handler — fires when files land in horizontal/ or vertical/.
# Pipeline: slug rename → Printify dry-run plan.
# Live publishing is intentionally manual: python3 printify/printify_publisher.py --live
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

  echo "--- Auto-logging curated images to feedback loop ---"
  python3 feedback_agent.py --auto-log site/src/assets/gallery/horizontal
  python3 feedback_agent.py --auto-log site/src/assets/gallery/vertical

  echo "--- Printify dry-run plan ---"
  python3 printify/printify_publisher.py --dry-run 2>&1 || true

  echo "=== To publish: python3 printify/printify_publisher.py --live ==="
} >> "$LOG" 2>&1
