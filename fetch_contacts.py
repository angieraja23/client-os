#!/usr/bin/env python3
"""
Client Acquisition OS — LinkedIn Contact Fetcher
Uses Google X-Ray search (no login required)
Run: python3 fetch_contacts.py
"""
import json, urllib.request, urllib.parse, re, hashlib, os, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR   = Path(__file__).parent
HTML_FILE  = BASE_DIR / "index.html"
SEEN_FILE  = BASE_DIR / "data" / "seen_contacts.json"
LOG_FILE   = BASE_DIR / "data" / "refresh_log.txt"

# ── X-Ray searches — Amazon agency founders only ──────────────────
SEARCHES = [
    'site:linkedin.com/in "amazon agency" "founder" "operations"',
    'site:linkedin.com/in "amazon agency" "co-founder"',
    'site:linkedin.com/in "amazon agency" founder CEO',
    'site:linkedin.com/in "ecommerce agency" "founder" operations',
    'site:linkedin.com/in "amazon seller" "founder" COO',
    'site:linkedin.com/in "FBA agency" founder',
    'site:linkedin.com/in "amazon brand" "founder" operations',
    'site:linkedin.com/in "amazon marketing agency" founder',
    'site:linkedin.com/in "ecommerce operations" founder CEO',
    'site:linkedin.com/in "amazon consulting" "founder" OR "co-founder"',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

def contact_id(linkedin_url):
    return hashlib.md5(linkedin_url.strip().lower().encode()).hexdigest()[:12]

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    with open(LOG_FILE, 'a') as f: f.write(line + '\n')

def google_xray(query):
    q = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={q}&num=10"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')

        contacts = []
        # Find all LinkedIn /in/ URLs
        urls = re.findall(
            r'https?://(?:www\.|[a-z]{2}\.)?linkedin\.com/in/[a-zA-Z0-9_%-]+',
            html
        )
        # Find name + title snippets near those URLs
        # Pattern: "Name - Title · Company"
        snippets = re.findall(
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+)\s*[-–]\s*([^<\n]{10,80})',
            html
        )

        seen_urls = set()
        for i, url in enumerate(urls[:8]):
            # Clean URL
            url = url.split('?')[0].rstrip('/')
            if url in seen_urls or '/in/search' in url:
                continue
            seen_urls.add(url)

            name = ''
            title = ''
            company = ''

            if i < len(snippets):
                name = snippets[i][0].strip()
                detail = snippets[i][1].strip()
                # Split "Title · Company" or "Title at Company"
                if '·' in detail:
                    parts = detail.split('·')
                    title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else ''
                elif ' at ' in detail.lower():
                    parts = re.split(r' at ', detail, flags=re.IGNORECASE)
                    title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else ''
                else:
                    title = detail

            if url:
                contacts.append({
                    'id':        contact_id(url),
                    'name':      name or 'LinkedIn Contact',
                    'title':     title,
                    'company':   company,
                    'linkedin':  url,
                    'source':    'X-Ray',
                    'stage':     'lead',
                    'revenue':   0,
                    'location':  '',
                    'dateFound': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                    'notes':     []
                })
        return contacts
    except Exception as e:
        log(f"  ⚠ Error: {e}")
        return []

def inject_contacts_into_html(new_contacts):
    with open(HTML_FILE) as f: html = f.read()

    # Find existing SEED contacts
    m = re.search(r'const SEED = (\[.*?\]);', html, re.DOTALL)
    existing = json.loads(m.group(1)) if m else []

    existing_li = {c.get('linkedin','').strip().lower() for c in existing if c.get('linkedin')}
    added = 0

    for c in new_contacts:
        li = c.get('linkedin','').strip().lower()
        if li and li not in existing_li:
            # Assign a new numeric id
            max_id = max((x.get('id',0) for x in existing if isinstance(x.get('id'),int)), default=50)
            c['id'] = max_id + 1
            existing.append(c)
            existing_li.add(li)
            added += 1

    new_seed = 'const SEED = ' + json.dumps(existing, indent=2) + ';'
    html = re.sub(r'const SEED = \[.*?\];', new_seed, html, flags=re.DOTALL)

    with open(HTML_FILE, 'w') as f: f.write(html)
    return added

def deploy():
    log("  Deploying to Vercel...")
    result = subprocess.run(
        ['vercel', '--prod', '--yes'],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    if result.returncode == 0:
        m = re.search(r'https://[^\s]+\.app', result.stdout + result.stderr)
        log(f"  ✅ Live: {m.group(0) if m else 'deployed'}")
    else:
        log(f"  ❌ Deploy failed: {result.stderr[:200]}")

def main():
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    log("=" * 50)
    log("LinkedIn Contact Fetch starting")

    seen = set(json.load(open(SEEN_FILE)) if SEEN_FILE.exists() else [])
    all_new = []

    for i, query in enumerate(SEARCHES):
        log(f"  Searching: {query[:60]}...")
        contacts = google_xray(query)
        new = [c for c in contacts if c['id'] not in seen]
        all_new.extend(new)
        seen.update(c['id'] for c in new)
        log(f"    → {len(new)} new contacts")
        # Polite delay to avoid Google rate limiting
        if i < len(SEARCHES) - 1:
            time.sleep(3)

    with open(SEEN_FILE, 'w') as f: json.dump(list(seen), f)

    if not all_new:
        log("No new contacts found — skipping deploy")
        print("\nNo new contacts to add today. Try again tomorrow.")
        return

    added = inject_contacts_into_html(all_new)
    log(f"Added {added} new contacts to the app")

    deploy()
    log("Done.\n")
    print(f"\n✅ Added {added} new LinkedIn contacts to your pipeline!")

if __name__ == '__main__':
    main()
