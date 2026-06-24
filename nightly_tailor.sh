#!/bin/bash
# Tailor resumes for all 'spotted' jobs in the pipeline.
set +e  # Don't exit on individual failures

LOG=~/Projects/client-os/data/cron.log
echo "=== Tailor started: $(date) ===" >> "$LOG"

source ~/.zshrc 2>/dev/null || true

# Get all spotted job IDs
JOB_IDS=$(/usr/bin/python3 -c "
import json
jobs = json.load(open('/Users/openclaw/Projects/client-os/data/jobs.json'))
ids = [j['id'] for j in jobs if j.get('stage') == 'spotted']
print(' '.join(ids))
")

COUNT=0
FAILED=0
for ID in $JOB_IDS; do
  if /usr/bin/python3 ~/job-search-agent/resume_tailor.py --job-id "$ID" >> "$LOG" 2>&1; then
    COUNT=$((COUNT+1))
  else
    FAILED=$((FAILED+1))
  fi
  sleep 7  # Pace Gemini API free tier (10/min)
done

echo "=== Tailor complete: $COUNT tailored, $FAILED failed at $(date) ===" >> "$LOG"
