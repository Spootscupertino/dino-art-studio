#!/usr/bin/env bash
# Install three launchd agents:
#   com.jurassinkart.web-sync      — category folders → Vercel
#   com.jurassinkart.printify-sync — horizontal/vertical → Printify
#   com.jurassinkart.hero-sync     — hero reel folder → Vercel (drop mp4s in)
#
# Run once:    bash tools/install_watcher.sh
# Uninstall:   bash tools/install_watcher.sh --uninstall

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GALLERY_ROOT="$ROOT/site/src/assets/gallery"
HERO_DIR="$ROOT/site/public/assets/hero"
LOG_DIR="$ROOT/tools/logs"
AGENTS_DIR="$HOME/Library/LaunchAgents"

WEB_LABEL="com.jurassinkart.web-sync"
PRINTIFY_LABEL="com.jurassinkart.printify-sync"
HERO_LABEL="com.jurassinkart.hero-sync"
WEB_PLIST="$AGENTS_DIR/$WEB_LABEL.plist"
PRINTIFY_PLIST="$AGENTS_DIR/$PRINTIFY_LABEL.plist"
HERO_PLIST="$AGENTS_DIR/$HERO_LABEL.plist"

WEB_CATEGORIES=(predators herbivores marine aerial flora_arthropods)
PRINTIFY_CATEGORIES=(horizontal vertical)
ALL_CATEGORIES=("${WEB_CATEGORIES[@]}" "${PRINTIFY_CATEGORIES[@]}")

# ---------- uninstall ----------

if [ "${1:-}" = "--uninstall" ]; then
  for plist in "$WEB_PLIST" "$PRINTIFY_PLIST" "$HERO_PLIST"; do
    if [ -f "$plist" ]; then
      launchctl unload "$plist" 2>/dev/null || true
      rm "$plist"
      echo "Uninstalled: $(basename "$plist" .plist)"
    fi
  done
  exit 0
fi

# ---------- pre-flight ----------

if [ ! -d "$GALLERY_ROOT" ]; then
  echo "ERROR: $GALLERY_ROOT not found." >&2
  exit 1
fi

for cat in "${ALL_CATEGORIES[@]}"; do
  mkdir -p "$GALLERY_ROOT/$cat"
done

mkdir -p "$LOG_DIR" "$AGENTS_DIR" "$HERO_DIR"
chmod +x "$ROOT/tools/web_sync.sh" "$ROOT/tools/printify_sync.sh" "$ROOT/tools/hero_sync.sh"

# ---------- helper: write one plist ----------

write_plist() {
  local plist="$1"
  local label="$2"
  local script="$3"
  shift 3
  local watch_dirs=("$@")

  launchctl unload "$plist" 2>/dev/null || true

  local watch_xml=""
  for dir in "${watch_dirs[@]}"; do
    watch_xml+="    <string>$dir</string>"$'\n'
  done

  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$script</string>
  </array>

  <key>WatchPaths</key>
  <array>
${watch_xml}  </array>

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

  launchctl load "$plist"
}

# ---------- install web-sync agent ----------

WEB_WATCH_DIRS=()
for cat in "${WEB_CATEGORIES[@]}"; do
  WEB_WATCH_DIRS+=("$GALLERY_ROOT/$cat")
done
write_plist "$WEB_PLIST" "$WEB_LABEL" "$ROOT/tools/web_sync.sh" "${WEB_WATCH_DIRS[@]}"

# ---------- install printify-sync agent ----------

PRINTIFY_WATCH_DIRS=()
for cat in "${PRINTIFY_CATEGORIES[@]}"; do
  PRINTIFY_WATCH_DIRS+=("$GALLERY_ROOT/$cat")
done
write_plist "$PRINTIFY_PLIST" "$PRINTIFY_LABEL" "$ROOT/tools/printify_sync.sh" "${PRINTIFY_WATCH_DIRS[@]}"

# ---------- install hero-sync agent ----------

write_plist "$HERO_PLIST" "$HERO_LABEL" "$ROOT/tools/hero_sync.sh" "$HERO_DIR"

# ---------- summary ----------

echo
echo "Installed three watchers:"
echo
echo "  $WEB_LABEL"
echo "  → Website pipeline (slug rename + products.json + Vercel push)"
for cat in "${WEB_CATEGORIES[@]}"; do
  echo "    $GALLERY_ROOT/$cat"
done
echo "  Log: $LOG_DIR/web_sync.log"
echo
echo "  $PRINTIFY_LABEL"
echo "  → Printify pipeline (slug rename + dry-run plan)"
for cat in "${PRINTIFY_CATEGORIES[@]}"; do
  echo "    $GALLERY_ROOT/$cat"
done
echo "  Log: $LOG_DIR/printify_sync.log"
echo
echo "  $HERO_LABEL"
echo "  → Hero reel (drop .mp4s here → commit + Vercel push)"
echo "    $HERO_DIR"
echo "  Log: $LOG_DIR/hero_sync.log"
echo
echo "Uninstall: bash tools/install_watcher.sh --uninstall"
