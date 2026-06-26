#!/usr/bin/env python3
"""Daily check: nudge Angie to follow up on jobs applied 3 and 7 days ago."""
import json, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

JOBS_FILE = Path.home() / "Projects/client-os/data/jobs.json"
CONFIG = Path.home() / ".openclaw/openclaw.json"
CHAT_ID = "2043351131"

def get_bot_token():
    return json.load(open(CONFIG))["channels"]["telegram"]["botToken"]

def send(text):
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true"
    }).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def main():
    jobs = json.load(open(JOBS_FILE))
    today = datetime.now(timezone.utc).date()

    nudges = []
    for j in jobs:
        if j.get("stage") != "applied":
            continue
        applied_date = j.get("appliedDate")
        if not applied_date:
            continue
        try:
            ad = datetime.strptime(applied_date, "%Y-%m-%d").date()
        except:
            continue
        days = (today - ad).days
        if days == 3:
            nudges.append((j, 3))
        elif days == 7:
            nudges.append((j, 7))

    if not nudges:
        return

    msg = "🔔 <b>Follow-up reminders</b>\n"
    for j, days in nudges:
        if days == 3:
            msg += f"\n📌 <b>{j['company']}</b> — applied 3 days ago. Time to find the recruiter on LinkedIn and send a note.\n<i>{j['title']}</i>\n"
        else:
            msg += f"\n⏰ <b>{j['company']}</b> — 7 days, no response. Last nudge: try the hiring manager directly or move on.\n<i>{j['title']}</i>\n"
    send(msg)

if __name__ == "__main__":
    main()
