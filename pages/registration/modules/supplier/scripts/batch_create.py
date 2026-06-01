#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Supplier entries via API with randomized data.

Just paste your Bearer token and go.

Usage:
    python pages/registration/modules/supplier/scripts/batch_create.py
    python pages/registration/modules/supplier/scripts/batch_create.py --count 20
    python pages/registration/modules/supplier/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import time
import json

# Add project root to path (supplier/scripts → supplier → modules → registration → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.supplier.data.supplier_data import generate_supplier_api_payload

# Default config — override with --token and --count flags
TENANT_ID = "599"
DEFAULT_COUNT = 10


def parse_args():
    """Parse simple --key value args from sys.argv."""
    args = {
        "token": None,
        "count": DEFAULT_COUNT,
        "dry_run": False,
    }
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
    """Create multiple Supplier entries and report stats."""
    success = 0
    fail = 0
    states_used = []
    districts_used = []
    ownerships_used = []
    start = time.time()

    print("=" * 70)
    print(f"  SUPPLIER BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_supplier_api_payload()
        addr = payload['children'][1]['details'][0]
        bank = payload['children'][2]['details'][0]

        state = addr.get('state_ref_id_id')
        district = addr.get('district_ref_id_id')
        ownership = payload.get('ownership_status_ref_id')
        name = payload['name']

        states_used.append(state)
        districts_used.append(district)
        ownerships_used.append(ownership)

        if dry_run:
            print(f'  [{i+1:2d}] [DRY] {name:40s} | State={state:3d} Dist={district:3d} Own={ownership}')
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            sid = result.get('id', '?')
            print(f'  [{i+1:2d}] OK  {name:40s} | ID={sid} State={state:3d} Own={ownership}')
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
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  States:      {sorted(set(states_used))} ({len(set(states_used))} unique)")
    print(f"  Districts:   {sorted(set(districts_used))} ({len(set(districts_used))} unique)")
    print(f"  Ownership:   {sorted(set(ownerships_used))} ({len(set(ownerships_used))} unique)")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  SUPPLIER BATCH CREATE")
        print("=" * 70)
        print()
        print("  No token provided. Get it from:")
        print("  1. Open https://rhythmerp.algorhythms.in in Chrome")
        print("  2. DevTools → Network → click any page")
        print("  3. Find any /core/ request → copy Authorization header")
        print("  4. Paste the token value (after 'Bearer ')")
        print()
        token = input("  Token: ").strip()
        if not token:
            print("  No token entered. Exiting.")
            return

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)

    # Quick auth check
    result = client.list_entries("Supplier", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
