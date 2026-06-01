#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Tax Authority entries via API with realistic Indian data.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/tax_authority/scripts/batch_create.py
    python pages/common_settings/modules/tax_authority/scripts/batch_create.py --count 20
    python pages/common_settings/modules/tax_authority/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import time

# Add project root to path (tax_authority/scripts → tax_authority → modules → common_settings → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.tax_authority.data.tax_authority_data import generate_tax_authority_api_payload

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
    countries_used = []
    start = time.time()

    print("=" * 70)
    print(f"  TAX AUTHORITY BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_tax_authority_api_payload()
        name = payload.get("name", "?")
        tax_type_id = payload.get("tax_type_ref_id")
        country_id = payload.get("country_ref_id")

        countries_used.append(country_id)

        if dry_run:
            print(f'  [{i+1:2d}] [DRY] {name:45s} | TaxTypeID={tax_type_id} CountryID={country_id}')
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            sid = result.get('id', '?')
            print(f'  [{i+1:2d}] OK  {name:45s} | ID={sid} CountryID={country_id}')
            success += 1
        else:
            print(f'  [{i+1:2d}] FAIL {name:45s}')
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    unique_countries = [c for c in set(countries_used) if c is not None]
    print(f"  Countries:   {sorted(unique_countries)} ({len(unique_countries)} unique)")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  TAX AUTHORITY BATCH CREATE")
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

    result = client.list_entries("Tax Authority", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
