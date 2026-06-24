#!/usr/bin/env python3
"""Clean up jobs.json based on Angie's filters: NY/remote, e-commerce industry, last 3 days."""
import json
from datetime import datetime, timedelta
from pathlib import Path

JOBS_FILE = Path.home() / "Projects/client-os/data/jobs.json"
SEEN_FILE = Path.home() / "Projects/client-os/data/seen_jobs.json"

# Load jobs
jobs = json.load(open(JOBS_FILE))
total_before = len(jobs)

# Filter 1: Location — NY/5 boroughs or remote
NY_TERMS = ['new york', 'ny', 'brooklyn', 'queens', 'bronx', 'manhattan', 'staten island', 'remote', 'work from home', 'anywhere']
def is_local_or_remote(j):
    loc = (j.get('location') or '').lower()
    title = (j.get('title') or '').lower()
    if not loc and 'remote' in title:
        return True
    if not loc:
        return False
    return any(term in loc for term in NY_TERMS)

# Filter 2: Industry — e-commerce, Amazon, agencies, DTC, brand, retail, marketing
INDUSTRY_TERMS = [
    'amazon', 'ecommerce', 'e-commerce', 'shopify', 'dtc', 'd2c', 'direct-to-consumer',
    'agency', 'brand', 'marketplace', 'seller', 'fba', 'retail', 'consumer',
    'cpg', 'marketing', 'digital', 'channel', 'fulfillment', 'logistics',
    'chief of staff', 'coo', 'head of operations', 'director of operations',
    'vp operations', 'business operations', 'startup', 'saas'
]
EXCLUDE_TERMS = [
    'restaurant', 'food', 'beverage', 'hotel', 'hospitality', 'nursing', 'nurse',
    'medical', 'healthcare', 'clinical', 'patient', 'construction', 'property',
    'waste', 'warehouse worker', 'driver', 'maintenance', 'janitorial',
    'security guard', 'retail store', 'store manager', 'shift manager',
    'cashier', 'server', 'cook', 'kitchen', 'overnight'
]
def is_relevant_industry(j):
    text = (j.get('title','') + ' ' + j.get('company','') + ' ' + j.get('query','')).lower()
    if any(ex in text for ex in EXCLUDE_TERMS):
        return False
    return any(term in text for term in INDUSTRY_TERMS)

# Filter 3: Posted in last 3 days
cutoff = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
def is_recent(j):
    return j.get('dateFound', '') >= cutoff

# Apply all filters but preserve already-applied/interviewing/offer jobs
KEEP_STAGES = ['applied', 'interviewing', 'offer']
filtered = []
removed_breakdown = {'old': 0, 'wrong_location': 0, 'wrong_industry': 0}
for j in jobs:
    if j.get('stage') in KEEP_STAGES:
        filtered.append(j)
        continue
    if not is_recent(j):
        removed_breakdown['old'] += 1
        continue
    if not is_local_or_remote(j):
        removed_breakdown['wrong_location'] += 1
        continue
    if not is_relevant_industry(j):
        removed_breakdown['wrong_industry'] += 1
        continue
    filtered.append(j)

# Save filtered jobs
json.dump(filtered, open(JOBS_FILE, 'w'), indent=2)

# Reset seen_jobs to only include kept jobs (so removed ones can be re-scraped if criteria change)
kept_ids = {j['id'] for j in filtered}
try:
    seen = json.load(open(SEEN_FILE))
    seen_filtered = {k: v for k, v in seen.items() if k in kept_ids}
    json.dump(seen_filtered, open(SEEN_FILE, 'w'), indent=2)
except:
    pass

print(f"\n=== Cleanup Complete ===")
print(f"Before: {total_before} jobs")
print(f"After:  {len(filtered)} jobs")
print(f"Removed: {total_before - len(filtered)}")
print(f"  Too old (>3 days):    {removed_breakdown['old']}")
print(f"  Wrong location:       {removed_breakdown['wrong_location']}")
print(f"  Wrong industry:       {removed_breakdown['wrong_industry']}")
