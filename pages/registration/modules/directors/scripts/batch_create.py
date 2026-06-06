#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Director entries via API with randomized data.

Just paste your Bearer token and go.

Usage:
    python pages/registration/modules/directors/scripts/batch_create.py
    python pages/registration/modules/directors/scripts/batch_create.py --count 20
    python pages/registration/modules/directors/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import time

# Add project root to path (directors/scripts → directors → modules → registration → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.directors.data.directors_data import generate_directors_api_payload

TENANT_ID = "599"
DEFAULT_COUNT = 10


def parse_args():
    args = {"token": None, "count": DEFAULT_COUNT, "dry_run": False}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--token" and i + 1 < len(sys.argv):
            args["token"] = sys.argv[i + 1]
            i += 2
        elif arg == "--count" and i + 1 < len(sys.argv):
            args["count"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--dry-run":
            args["dry_run"] = True
            i += 1
        else:
            i += 1
    return args


def batch_create(client, count, dry_run=False):
    success = 0
    fail = 0
    designations_used = []
    qualifications_used = []
    prefixes_used = []
    kyc_docs_used = []
    start = time.time()

    print("=" * 70)
    print(f"  DIRECTORS BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_directors_api_payload()
        name = payload['name']
        prefix = payload.get('prefix_ref_id')
        desig = payload.get('designation')
        qual = payload.get('qualification_ref_id')
        age = payload.get('age')
        exp = payload.get('experience_in_years')
        kyc_rows = payload.get('children', [{}])[0].get('details', [])

        prefixes_used.append(prefix)
        designations_used.append(desig)
        qualifications_used.append(qual)
        for kr in kyc_rows:
            kyc_docs_used.append(kr.get('kyc_doc_id'))

        if dry_run:
            print(f'  [{i+1:2d}] [DRY] {name:40s} | Desig={desig} Qual={qual} Age={age} Exp={exp}')
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            mid = result.get('id', '?')
            print(f'  [{i+1:2d}] OK  {name:40s} | ID={mid} Desig={desig} Age={age}')
            success += 1
        else:
            print(f'  [{i+1:2d}] FAIL {name:40s}')
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:       {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:          {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  Prefixes:      {sorted(set(p for p in prefixes_used if p))} ({len(set(p for p in prefixes_used if p))} unique)")
    print(f"  Designations:  {sorted(set(d for d in designations_used if d))} ({len(set(d for d in designations_used if d))} unique)")
    print(f"  Qualifications: {sorted(set(q for q in qualifications_used if q))} ({len(set(q for q in qualifications_used if q))} unique)")
    print(f"  KYC docs:      {sorted(set(k for k in kyc_docs_used if k))} ({len(set(k for k in kyc_docs_used if k))} unique)")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  DIRECTORS BATCH CREATE")
        print("=" * 70)
        print()
        print("  No token provided. Get it from:")
        print("  1. Open https://rhythmerp.algorhythms.in in Chrome")
        print("  2. DevTools -> Network -> click any page")
        print("  3. Find any /core/ request -> copy Authorization header")
        print("  4. Paste the token value (after 'Bearer ')")
        print()
        token = input("  Token: ").strip()
        if not token:
            print("  No token entered. Exiting.")
            return

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)

    result = client.list_entries("Directors", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
