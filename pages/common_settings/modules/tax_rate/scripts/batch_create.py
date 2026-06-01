#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Tax Rate entries via API with randomized data.

Uses realistic Indian GST slabs (5, 12, 18, 28%) and HSN codes.
Each Tax Rate entry includes a nested sub-table with HSN + Tax Rate rows.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/tax_rate/scripts/batch_create.py
    python pages/common_settings/modules/tax_rate/scripts/batch_create.py --count 10
    python pages/common_settings/modules/tax_rate/scripts/batch_create.py --token eyJhbGci...
    python pages/common_settings/modules/tax_rate/scripts/batch_create.py --dry-run
"""

import sys
import os
import time
import json

# Add project root to path (tax_rate/scripts -> tax_rate -> modules -> common_settings -> pages -> project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.tax_rate.data.tax_rate_data import generate_tax_rate_api_payload

TENANT_ID = "599"
DEFAULT_COUNT = 10
SCREEN_NAME = "Tax Rate"


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
    tax_rates_used = []
    hsn_counts = []
    start = time.time()

    print("=" * 70)
    print(f"  TAX RATE BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_tax_rate_api_payload()
        name = payload.get("tax_rate_name", "?")
        details = payload.get("children", [{}])[0].get("details", [])
        detail_count = len(details)
        revision = payload.get("revision_status", "?")
        from_dt = payload.get("from_date", "?")

        # Collect stats
        for d in details:
            tax_rates_used.append(d.get("tax_rate"))
        hsn_counts.append(detail_count)

        if dry_run:
            rates_str = ", ".join(f"{d.get('tax_rate')}%" for d in details)
            print(f"  [{i+1:2d}] [DRY] {name:45s} | Rev={revision:10s} Rows={detail_count} Rates=[{rates_str}]")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            rid = result.get("id", "?")
            rates_str = ", ".join(f"{d.get('tax_rate')}%" for d in details)
            print(f"  [{i+1:2d}] OK  {name:45s} | ID={rid} Rev={revision:10s} Rows={detail_count} Rates=[{rates_str}]")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {name:45s} | Rev={revision} Rows={detail_count}")
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
    if tax_rates_used:
        unique_rates = sorted(set(tax_rates_used))
        print(f"  Tax rates:   {unique_rates} ({len(unique_rates)} unique slabs)")
    print(f"  HSN rows:    min={min(hsn_counts)}, max={max(hsn_counts)}, avg={sum(hsn_counts)/len(hsn_counts):.1f}")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  TAX RATE BATCH CREATE")
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

    # Validate token with a list_entries call
    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    # Show existing count
    existing = result.get("screenmatlistingdata_set", [])
    total_count = result.get("count", len(existing))
    print(f"  Existing Tax Rate entries: {total_count}")
    print()

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
