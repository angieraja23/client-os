#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "======================================"
echo "  Client Acquisition OS — Setup"
echo "======================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 not found. Install from python.org"
  exit 1
fi

# Check Vercel CLI
if ! command -v vercel &>/dev/null; then
  echo "📦 Installing Vercel CLI..."
  npm install -g vercel
fi

mkdir -p "$DIR/data"

# Create macOS LaunchAgent to run daily at 7am
PLIST="$HOME/Library/LaunchAgents/com.caos.dailyrefresh.plist"
cat > "$PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.caos.dailyrefresh</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DIR/daily_refresh.py</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>7</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$DIR/data/refresh_log.txt</string>
  <key>StandardErrorPath</key>
  <string>$DIR/data/refresh_log.txt</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLISTEOF

# Load the scheduler
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "✅ Daily refresh scheduled for 7:00 AM every day"
echo "✅ Setup complete!"
echo ""
echo "To run manually anytime:"
echo "  python3 $DIR/daily_refresh.py"
echo ""
echo "To check the log:"
echo "  cat $DIR/data/refresh_log.txt"
echo ""
