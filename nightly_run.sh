#!/bin/bash
# Nightly Client OS refresh: scrape jobs, commit, push, deploy
set -e

LOG=~/Projects/client-os/data/cron.log
echo "=== Run started: $(date) ===" >> "$LOG"

cd ~/Projects/client-os || exit 1

# Load shell environment so GITLAB_TOKEN and PATH are available
source ~/.zshrc 2>/dev/null || true

# Run scraper
/usr/bin/python3 daily_refresh.py --force >> "$LOG" 2>&1

# Commit if there are changes
if [[ -n $(git status -s data/) ]]; then
  git add data/ >> "$LOG" 2>&1
  git commit -m "Nightly auto-sync $(date +%Y-%m-%d)" >> "$LOG" 2>&1
  git push origin main >> "$LOG" 2>&1
  git push github main >> "$LOG" 2>&1
  /opt/homebrew/bin/vercel --prod --yes --cwd ~/Projects/client-os >> "$LOG" 2>&1
  echo "=== Deployed: $(date) ===" >> "$LOG"
else
  echo "=== No new jobs to commit: $(date) ===" >> "$LOG"
fi

# Always tailor resumes for any spotted jobs missing a tailored DOCX
~/Projects/client-os/nightly_tailor.sh
