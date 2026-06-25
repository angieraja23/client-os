#!/bin/bash
# Nightly Client OS refresh — designed to work in minimal cron environment
set -uo pipefail  # Removed -e so failures don't kill the whole script silently

# Hardcoded PATH for cron (it doesn't inherit from .zshrc)
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Load tokens from .zshrc directly via bash sourcing
export GITLAB_TOKEN="$(bash -c 'source ~/.zshrc 2>/dev/null; echo $GITLAB_TOKEN')"
export GITHUB_TOKEN="$(bash -c 'source ~/.zshrc 2>/dev/null; echo $GITHUB_TOKEN')"
export ANTHROPIC_API_KEY="$(bash -c 'source ~/.zshrc 2>/dev/null; echo $ANTHROPIC_API_KEY')"

LOG=~/Projects/client-os/data/cron.log
echo "=== Run started: $(date) ===" >> "$LOG"
echo "PATH=$PATH" >> "$LOG"
echo "GITLAB_TOKEN=$([ -n "$GITLAB_TOKEN" ] && echo 'SET' || echo 'MISSING')" >> "$LOG"
echo "GITHUB_TOKEN=$([ -n "$GITHUB_TOKEN" ] && echo 'SET' || echo 'MISSING')" >> "$LOG"
echo "ANTHROPIC_API_KEY=$([ -n "$ANTHROPIC_API_KEY" ] && echo 'SET' || echo 'MISSING')" >> "$LOG"

cd ~/Projects/client-os || { echo "FAIL: cd failed" >> "$LOG"; exit 1; }

# Run scraper
echo "--- Running scraper ---" >> "$LOG"
/usr/bin/python3 daily_refresh.py --force >> "$LOG" 2>&1
SCRAPE_EXIT=$?
echo "Scraper exit code: $SCRAPE_EXIT" >> "$LOG"

# Commit if there are changes
if [[ -n $(git status -s data/) ]]; then
  echo "--- Committing and pushing ---" >> "$LOG"
  git add data/ >> "$LOG" 2>&1
  git commit -m "Nightly auto-sync $(date +%Y-%m-%d)" >> "$LOG" 2>&1
  git push origin main >> "$LOG" 2>&1
  git push github main >> "$LOG" 2>&1
  /opt/homebrew/bin/vercel --prod --yes --cwd ~/Projects/client-os >> "$LOG" 2>&1
  echo "=== Deployed: $(date) ===" >> "$LOG"
else
  echo "=== No changes: $(date) ===" >> "$LOG"
fi

# Copy tailored resumes into web-accessible folder
mkdir -p ~/Projects/client-os/resumes/tailored
cp -u ~/job-search-agent/resumes/tailored/*.docx ~/Projects/client-os/resumes/tailored/ 2>/dev/null || true

# Always run tailor
echo "--- Running tailor ---" >> "$LOG"
~/Projects/client-os/nightly_tailor.sh >> "$LOG" 2>&1
echo "=== Run finished: $(date) ===" >> "$LOG"
