#/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Director entries via API with randomized data.

Usage:
    python pages/registration/modules/directors/scripts/batch_create.py --token <jwt> --tenant <id> --count <n>
    python pages/registration/modules/directors/scripts/batch_create.py --token eyJhbGci... --tenant 711 --count 10
"""

import sys
import os
import argparse
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.directors.data.directors_data import generate_directors_api_payload


SCREEN_NAME = "Directors"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Director entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    return parser.parse_args()


def batch_create(client, count, dry_run=False):
    success = 0
    fail = 0
    prefixes_used = []
    designations_used = []
    qualifications_used = []
    kyc_docs_used = []
    start = time.time()

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE -- {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_directors_api_payload()
        name = payload.get("name", "")
        prefix = payload.get("prefix")
        designation = payload.get("designation")
        qualification = payload.get("qualification")
        kyc_doc = payload.get("kyc_document_type")

        prefixes_used.append(prefix)
        designations_used.append(designation)
        qualifications_used.append(qualification)
        kyc_docs_used.append(kyc_doc)

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {name:40s} | Prefix={prefix} Desig={designation}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            did = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {name:40s} | ID={did} Prefix={prefix} Desig={designation}")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {name:40s}")
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


def prompt_missing_args(args):
    if not args.token:
        print("\n  No token provided. Open DevTools -> Network -> any /core/ request -> Authorization header")
        args.token = input("  Token: ").strip()
        if not args.token:
            print("  No token entered. Exiting.")
            sys.exit(1)
    if not args.tenant:
        args.tenant = input("  Tenant ID (e.g., 711): ").strip()
        if not args.tenant:
            print("  No tenant entered. Exiting.")
            sys.exit(1)
    if not args.count:
        count_str = input("  Count (default 10): ").strip()
        args.count = int(count_str) if count_str else 10
    return args


def main():
    args = parse_args()
    args = prompt_missing_args(args)
    client = RhythmERPAPIClient()
    client.login_from_browser(token=args.token, tenant_id=args.tenant)

    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        raw = client._last_raw_response
        if raw is not None:
            status = raw.status_code
            body = raw.text[:300]
            print()
            print(f"  API error: {status} -- {body}")
        else:
            print()
            print("  API error: No response received (network issue or ERP unreachable).")
        client.close()
        return

    batch_create(client, args.count, args.dry_run)
    client.close()


if __name__ == "__main__":
    main()
