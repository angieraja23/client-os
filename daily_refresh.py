#!/usr/bin/env python3
"""
Client Acquisition OS — Weekly Refresh (runs every Monday at 7am)
Jobs:     SerpAPI Google Jobs → writes data/jobs.json (NEVER touches HTML)
Contacts: SerpAPI Google X-Ray → writes to HTML SEED
Run manually: python3 daily_refresh.py --force
"""
import json, urllib.request, urllib.parse
import hashlib, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR  = Path(__file__).parent
HTML_FILE = BASE_DIR / "index.html"
DATA_DIR  = BASE_DIR / "data"
JOBS_FILE = DATA_DIR / "jobs.json"
LOG_FILE  = DATA_DIR / "refresh_log.txt"

SERPAPI_KEY = "44a8d64c994f218da81170ca653427ddfe12baac50191c4f6c06b848ac6bd750"

JOB_QUERIES = [
    'Operations Manager',
    'Chief of Staff',
    'Ecommerce Operations Manager',
    'Amazon Account Manager',
    'Client Services Manager',
    'Agency Operations Manager',
    'Business Operations Manager',
    'Implementation Manager',
]

CONTACT_SEARCHES = [
    'site:linkedin.com/in "amazon agency" "founder" operations',
    'site:linkedin.com/in "amazon agency" "co-founder"',
    'site:linkedin.com/in "amazon agency" founder CEO',
    'site:linkedin.com/in "ecommerce agency" founder operations',
    'site:linkedin.com/in "FBA agency" founder',
    'site:linkedin.com/in "amazon seller" founder COO',
    'site:linkedin.com/in "amazon brand" founder operations',
    'site:linkedin.com/in "amazon marketing agency" founder',
    'site:linkedin.com/in "ecommerce operations" founder CEO',
    'site:linkedin.com/in "amazon consulting" founder OR co-founder',
]

GOOD_KEYWORDS = ['operations','amazon','ecommerce','account manager','chief of staff',
                 'coo','client success','client services','implementation','agency',
                 'project manager','fractional','marketplace','shopify','growth']
BAD_KEYWORDS  = ['payroll','supply chain','toxicology','clinical','government',
                 'military','defense','it operations','network operations',
                 'software engineer','developer','recruiter','staffing','java','python']
KEEP_TITLES   = ['founder','co-founder','ceo','coo','owner','president']

FEMALE_NAMES = {
    'amber','andrea','angela','ashley','brittany','caroline','charlotte',
    'christina','claire','dana','deborah','debra','diana','donna','elena',
    'elizabeth','emily','erica','erin','gabriela','helen','jennifer',
    'jessica','julia','karen','kate','katherine','kelly','kim','kimberly',
    'laura','lauren','linda','lisa','madison','maria','mary','melissa',
    'michelle','morgan','natalie','nicole','olivia','pamela','patricia',
    'rachel','rebecca','sarah','shannon','stephanie','susan','taylor',
    'tiffany','tracy','victoria','wendy','amy','anna','anne','annie',
    'barbara','beth','betty','bonnie','brenda','carol','cheryl','cindy',
    'crystal','cynthia','dawn','debbie','denise','elaine','emma','gina',
    'gloria','grace','hannah','heather','holly','irene','jackie','jane',
    'janet','janice','jean','joan','joanna','joyce','judy','julie',
    'madeline','margaret','martha','megan','melanie','miranda','nancy',
    'nina','norma','penny','rosa','rose','ruth','samantha','sandra',
    'sara','sharon','sheila','shirley','stacy','sue','tamara','tammy',
    'tanya','teresa','terri','tina','valerie','veronica','virginia','wanda'
}

def is_male_name(name):
    if not name: return True
    return name.strip().split()[0].lower() not in FEMALE_NAMES

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, 'a') as f: f.write(line + '\n')

def job_hash(title, company):
    return hashlib.md5(f"{title.lower().strip()}-{company.lower().strip()}".encode()).hexdigest()[:12]

def contact_hash(url):
    return hashlib.md5(url.strip().lower().encode()).hexdigest()[:12]

def serpapi(params):
    params['api_key'] = SERPAPI_KEY
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  SerpAPI error: {e}"); return {}

def is_relevant_job(title):
    tl = title.lower()
    if any(b in tl for b in BAD_KEYWORDS): return False
    return any(g in tl for g in GOOD_KEYWORDS)

def best_apply_link(job):
    opts = job.get('apply_options', [])
    for opt in opts:
        if 'linkedin' in opt.get('link', '').lower(): return opt['link']
    for opt in opts:
        if 'indeed' in opt.get('link', '').lower(): return opt['link']
    if opts: return opts[0].get('link', '')
    return job.get('share_link', '')

def quick_apply_label(link):
    l = link.lower()
    if 'linkedin' in l: return 'LinkedIn · Easy Apply'
    if 'indeed' in l: return 'Indeed · Easily Apply'
    return None

# ── JOBS → data/jobs.json (never touches HTML) ───────────────────
def run_jobs():
    log("── JOBS ─────────────────────────────────")
    seen_file = DATA_DIR / "seen_jobs.json"
    seen = set()
    if seen_file.exists():
        try: seen = set(json.load(open(seen_file)))
        except: pass

    # Load existing jobs from JSON file
    existing = []
    if JOBS_FILE.exists():
        try: existing = json.load(open(JOBS_FILE))
        except: pass
    existing_ids = {j.get('id', '') for j in existing}

    added = 0
    CHIPS = 'date_posted:week'

    searches = []
    for q in JOB_QUERIES:
        searches.append((q, '', 'Remote', CHIPS + ',work_from_home:1'))
        searches.append((q, 'New York,NY', 'New York', CHIPS))

    for query, location, loc_label, chips in searches:
        log(f"  {query} — {loc_label}")
        params = {'engine': 'google_jobs', 'q': query, 'chips': chips, 'num': 10}
        if location: params['location'] = location
        jobs = serpapi(params).get('jobs_results', [])
        log(f"    {len(jobs)} results")

        for j in jobs:
            title   = j.get('title', '').strip()
            company = j.get('company_name', '').strip()
            loc     = j.get('location', loc_label).strip()
            link    = best_apply_link(j)
            via     = j.get('via', '').replace('via ', '')
            salary  = ''
            for section in j.get('job_highlights', []):
                for item in section.get('items', []):
                    if '$' in item: salary = item[:60]; break

            if not title or not company: continue
            if not is_relevant_job(title): continue
            jid = job_hash(title, company)
            if jid in seen or jid in existing_ids: continue

            qa = quick_apply_label(link)
            existing.append({
                'id': jid, 'title': title, 'company': company,
                'location': loc, 'salary': salary, 'url': link,
                'source': qa if qa else (via or 'Google Jobs'),
                'query': query, 'stage': 'spotted',
                'dateFound': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'notes': []
            })
            seen.add(jid); existing_ids.add(jid); added += 1
            log(f"    + {title} @ {company} ({loc}){' [' + qa + ']' if qa else ''}")
        time.sleep(0.5)

    with open(seen_file, 'w') as f: json.dump(list(seen), f)

    # Write to jobs.json (NOT HTML)
    existing = existing[-300:]
    with open(JOBS_FILE, 'w') as f: json.dump(existing, f, indent=2)
    log(f"  Wrote {len(existing)} jobs to data/jobs.json ({added} new)")
    return added > 0

# ── CONTACTS → HTML SEED (this part works) ────────────────────────
def run_contacts():
    log("── CONTACTS ─────────────────────────────")
    seen_file = DATA_DIR / "seen_contacts.json"
    seen = set()
    if seen_file.exists():
        try: seen = set(json.load(open(seen_file)))
        except: pass

    with open(HTML_FILE) as f: html = f.read()
    start = html.find('const SEED = [')
    if start == -1: log("  SEED not found"); return False
    s = start + len('const SEED = ')
    depth = 0
    for j in range(s, len(html)):
        if html[j] == '[': depth += 1
        elif html[j] == ']':
            depth -= 1
            if depth == 0: end = j + 1; break

    seed_js   = html[s:end]
    seed_json = re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:', r'"\1":', seed_js)
    seed_json = re.sub(r',\s*([}\]])', r'\1', seed_json)
    existing  = json.loads(seed_json)
    existing_li = {c.get('linkedin', '').lower().rstrip('/') for c in existing if c.get('linkedin')}
    max_id = max((x.get('id', 0) for x in existing if isinstance(x.get('id'), int)), default=50)
    added = 0

    for query in CONTACT_SEARCHES:
        log(f"  {query[:55]}...")
        data = serpapi({'engine': 'google', 'q': query, 'num': 10})
        for item in data.get('organic_results', []):
            url = item.get('link', '').split('?')[0].rstrip('/')
            if 'linkedin.com/in/' not in url: continue
            title_text = item.get('title', '')
            snippet = item.get('snippet', '')
            name = ''
            m = re.match(r'^([A-Z][a-zA-Z\'\-]+(?: [A-Z][a-zA-Z\'\-]+)+)', title_text)
            if m: name = m.group(1).strip()
            role = company = ''
            for text in [title_text, snippet]:
                if ' - ' in text:
                    parts = text.split(' - ', 1)[1]
                    if ' | ' in parts:
                        sub = parts.split(' | ', 1)
                        role = sub[0].strip(); company = sub[1].strip()
                    elif ' at ' in parts.lower():
                        sub = re.split(r' at ', parts, flags=re.IGNORECASE, maxsplit=1)
                        role = sub[0].strip(); company = sub[1].strip() if len(sub) > 1 else ''
                    else: role = parts.strip()
                    break
            if not any(k in role.lower() for k in KEEP_TITLES): continue
            if not is_male_name(name): continue
            cid = contact_hash(url)
            li = url.lower()
            if cid in seen or li in existing_li: continue
            max_id += 1
            existing.append({
                'id': max_id, 'name': name or 'LinkedIn Contact',
                'title': role, 'company': company, 'linkedin': url,
                'source': 'LinkedIn', 'stage': 'lead', 'revenue': 0,
                'location': '',
                'dateFound': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'notes': []
            })
            seen.add(cid); existing_li.add(li); added += 1
            log(f"    + {name or 'Contact'} — {role} @ {company}")
        time.sleep(0.5)

    with open(seen_file, 'w') as f: json.dump(list(seen), f)

    if added:
        new_seed = 'const SEED = ' + json.dumps(existing, indent=2) + ';\n'
        html = html[:start] + new_seed + html[end + 1:]
        with open(HTML_FILE, 'w') as f: f.write(html)
        log(f"  Added {added} contacts (total {len(existing)})")
    else:
        log("  No new contacts this week")
    return added > 0

def deploy():
    log("── DEPLOYING via GitLab ──────────────────")
    try:
        subprocess.run(['git', 'add', '-A'], cwd=BASE_DIR)
        subprocess.run(['git', 'commit', '-m', 'Weekly refresh ' + datetime.now().strftime('%Y-%m-%d')], cwd=BASE_DIR)
        r = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd=BASE_DIR)
        if r.returncode == 0:
            log("  Pushed to GitLab")
        else:
            log("  Push done")
    except: pass
    r=subprocess.run(["vercel","--prod","--yes"],capture_output=True,text=True,cwd=BASE_DIR)
    if r.returncode==0: log("  Deployed to Vercel")
    else: log(f"  Deploy failed: {r.stderr[:200]}")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    force = '--force' in sys.argv
    if not force and datetime.now().weekday() != 0:
        print("Not Monday. Use --force to run anytime.")
        return
    log("=" * 50)
    log("Client Acquisition OS — Weekly Refresh")
    changed = run_jobs()
    changed = run_contacts() or changed
    if changed: deploy()
    else: log("Nothing new — skipping deploy")
    log("Done.\n")

if __name__ == '__main__':
    main()
