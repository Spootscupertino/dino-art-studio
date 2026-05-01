#!/usr/bin/env bash
# Install the launchd agent that watches site/src/assets/gallery/<category>/
# and runs sync_and_deploy.sh whenever a file is added, removed, or changed.
#
# launchd's WatchPaths does NOT recurse, so each category subfolder must be
# registered individually.
#
# Run once:  tools/install_watcher.sh
# Uninstall: tools/install_watcher.sh --uninstall

set -euo pipefail

LABEL="com.jurassinkart.sync-gallery"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GALLERY_ROOT="$ROOT/site/src/assets/gallery"
CATEGORIES=(predators herbivores marine aerial flora_arthropods horizontal vertical)
SCRIPT="$ROOT/tools/sync_and_deploy.sh"
LOG_DIR="$ROOT/tools/logs"

if [ "${1:-}" = "--uninstall" ]; then
  if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm "$PLIST"
    echo "Uninstalled $LABEL"
  else
    echo "No agent installed at $PLIST"
  fi
  exit 0
fi

if [ ! -d "$GALLERY_ROOT" ]; then
  echo "ERROR: gallery root $GALLERY_ROOT not found." >&2
  exit 1
fi

# Make sure every category subfolder exists so launchd can attach a watch.
for cat in "${CATEGORIES[@]}"; do
  mkdir -p "$GALLERY_ROOT/$cat"
done

mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"
chmod +x "$SCRIPT" "$ROOT/tools/sync_gallery.py"

# Stop any previous version before rewriting the plist.
launchctl unload "$PLIST" 2>/dev/null || true

# Build the WatchPaths XML block.
WATCH_PATHS_XML=""
for cat in "${CATEGORIES[@]}"; do
  WATCH_PATHS_XML+="    <string>$GALLERY_ROOT/$cat</string>"$'\n'
done

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$SCRIPT</string>
  </array>

  <key>WatchPaths</key>
  <array>
${WATCH_PATHS_XML}  </array>

  <key>RunAtLoad</key>
  <false/>

  <key>ThrottleInterval</key>
  <integer>10</integer>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/launchd.out</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchd.err</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>$HOME</string>
  </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST"

echo "Installed: $LABEL"
echo "Watching:"
for cat in "${CATEGORIES[@]}"; do
  echo "  $GALLERY_ROOT/$cat"
done
echo "Logs:      $LOG_DIR/sync.log"
echo
echo "Drop a file into any category subfolder and the gallery will auto-update + deploy."
echo "Uninstall later with: $0 --uninstall"
