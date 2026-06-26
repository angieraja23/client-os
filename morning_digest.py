#!/usr/bin/env python3
"""Send a Telegram digest of new jobs after each scrape. No AI — pure Telegram API."""
import json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

JOBS_FILE = Path.home() / "Projects/client-os/data/jobs.json"
CONFIG = Path.home() / ".openclaw/openclaw.json"
CHAT_ID = "2043351131"
DASHBOARD = "https://clientos.angieraja.com"

def get_bot_token():
    cfg = json.load(open(CONFIG))
    return cfg["channels"]["telegram"]["botToken"]

def send(text):
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def main():
    jobs = json.load(open(JOBS_FILE))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # New jobs found today, still in spotted stage
    new_jobs = [j for j in jobs if j.get("dateFound") == today and j.get("stage") == "spotted"]

    if not new_jobs:
        send("☀️ <b>Morning digest</b>\n\nNo new jobs today. Pipeline is current.")
        return

    targets = [j for j in new_jobs if j.get("priority")]
    regular = [j for j in new_jobs if not j.get("priority")]

    msg = f"☀️ <b>Morning digest — {len(new_jobs)} new jobs</b>\n"

    if targets:
        msg += f"\n⭐ <b>{len(targets)} TARGET agency match(es):</b>\n"
        for j in targets[:5]:
            sal = f" · {j['salary']}" if j.get("salary") else ""
            msg += f"• <b>{j['title']}</b> at {j['company']}{sal}\n"

    if regular:
        msg += f"\n<b>{len(regular)} other matches:</b>\n"
        for j in regular[:8]:
            track = "🔵" if j.get("track") == "amazon" else "🟣"
            msg += f"{track} {j['title']} at {j['company']}\n"

    msg += f"\n👉 <a href='{DASHBOARD}'>Open dashboard to apply</a>"
    send(msg)

if __name__ == "__main__":
    main()
