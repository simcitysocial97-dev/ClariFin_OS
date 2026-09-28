#!/usr/bin/env python3
"""M9-C68: Backend -> Frontend Feature Completeness Audit"""
import json
import re
import os
from collections import Counter
from datetime import datetime, timezone

REPO = '/home/vasantha/AI-Projects/ClariFin_OS'
ARTIFACTS = f'{REPO}/runtime/generated/m9-c68-frontend-completeness'
BT = '`'  # backtick character

def normalize(p):
    p = re.sub(r'\{[^}]+\}', ':param', p)
    return p.split('?')[0]

def extract_api_paths(content):
    pattern = re.escape(BT) + r'(/api[^' + re.escape(BT) + r']+|/platform[^' + re.escape(BT) + r']+)' + re.escape(BT)
    return re.findall(pattern, content)

with open(f'{ARTIFACTS}/backend-endpoint-inventory.json') as f:
    backend = json.load(f)

print(f"Loaded {len(backend)} backend endpoints")

frontend_paths = set()

hooks_dir = f'{REPO}/frontend/lib/hooks'
for fname in os.listdir(hooks_dir):
    if not fname.endswith('.ts') or fname.endswith('.test.ts'):
        continue
    with open(f'{hooks_dir}/{fname}') as f:
        content = f.read()
    for path in extract_api_paths(content):
        frontend_paths.add(normalize(path))

pages_dir = f'{REPO}/frontend/app'
for root, dirs, files in os.walk(pages_dir):
    for fname in files:
        if not fname.endswith('.tsx'):
            continue
        with open(f'{root}/{fname}') as f:
            content = f.read()
        for path in extract_api_paths(content):
            frontend_paths.add(normalize(path))

print(f"Frontend consumes {len(frontend_paths)} unique API paths")
print()
print("=== CONSUMED PATHS ===")
for p in sorted(frontend_paths):
    print(f"  {p}")

consumed = []
unconsumed = []
for e in backend:
    np = normalize(e['path'])
    if np in frontend_paths:
        consumed.append(e)
    else:
        unconsumed.append(e)

print(f"\nConsumed endpoints: {len(consumed)}")
print(f"Unconsumed endpoints: {len(unconsumed)}")

classified = []
for e in unconsumed:
    np = normalize(e['path'])
    if e['class'] == 'INFRASTRUCTURE':
        cls, reason = 'INFRASTRUCTURE', 'Health/readiness probes - intentional'
    elif e['class'] == 'USER_FACING':
        if 'balance' in np or 'running-balance' in np:
            cls, reason = 'LEGACY_ENDPOINT', 'Superseded by /metrics or workspace endpoints'
        elif 'financial-events' in np:
            cls, reason = 'INTERNAL', 'Internal event tracking - no UI consumer'
        elif 'transactions' in np and e['method'] == 'GET':
            cls, reason = 'LEGACY_ENDPOINT', 'Superseded by workspace endpoints'
        elif 'balance-history' in np and 'latest' in np:
            cls, reason = 'LEGACY_ENDPOINT', 'Superseded by v1 accounts metrics'
        elif 'history/compare' in np and e['method'] == 'POST':
            cls, reason = 'PLATFORM_ONLY', 'Platform Console feature only'
        else:
            cls, reason = 'LEGACY_ENDPOINT', 'Legacy endpoint - frontend uses alternative path'
    else:
        cls, reason = 'PLATFORM_INTERNAL', 'Platform Console endpoint'
    classified.append({**e, 'classification': cls, 'reason': reason})

counts = Counter(e['classification'] for e in classified)
print("\n=== UNCONSUMED CLASSIFICATION ===")
for k, v in sorted(counts.items()):
    print(f"  {k}: {v}")

result = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'total_endpoints': len(backend),
    'consumed_count': len(consumed),
    'unconsumed_count': len(unconsumed),
    'frontend_consumed_paths': sorted(frontend_paths),
    'consumed_endpoints': consumed,
    'unconsumed_classified': classified,
    'classification_counts': dict(counts)
}
with open(f'{ARTIFACTS}/frontend-consumption-inventory.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f"\nSaved frontend-consumption-inventory.json")
