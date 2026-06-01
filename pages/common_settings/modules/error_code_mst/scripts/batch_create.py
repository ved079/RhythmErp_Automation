#!/usr/bin/env python3
"""
batch_create.py
---------------
Create multiple Error Code Mst entries via API with realistic error codes.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/error_code_mst/scripts/batch_create.py
    python pages/common_settings/modules/error_code_mst/scripts/batch_create.py --count 20
    python pages/common_settings/modules/error_code_mst/scripts/batch_create.py --token eyJhbGci...

Note: Error Code Mst has a dropdown FK field (Error Code Type) with 4 fixed
      options: Farmer, Debit Note, Credit Note, Workflow. The FK IDs must be
      discovered from the live API first. Update ERROR_CODE_TYPE_IDS in
      error_code_mst_data.py before running this script, or pass them via
      --dropdown-ids flag.
"""

import sys
import os
import time
import json

# Add project root to path (error_code_mst/scripts → error_code_mst → modules → common_settings → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_error_code_mst_api_payload,
    ERROR_CODE_TYPE_IDS,
)

TENANT_ID = "599"
DEFAULT_COUNT = 10


def parse_args():
    args = {
        "token": None,
        "count": DEFAULT_COUNT,
        "dry_run": False,
        "dropdown_ids": None,
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
        elif arg == "--dropdown-ids" and i + 1 < len(sys.argv):
            try:
                args["dropdown_ids"] = json.loads(sys.argv[i + 1])
            except json.JSONDecodeError:
                print(f"  WARNING: Could not parse --dropdown-ids JSON: {sys.argv[i + 1]}")
            i += 2
        elif arg == "--dry-run":
            args["dry_run"] = True
            i += 1
        else:
            i += 1
    return args


def _check_dropdown_ids():
    """Check if ERROR_CODE_TYPE_IDS have been populated.
    Returns True if all 4 IDs are set, False otherwise."""
    missing = [k for k, v in ERROR_CODE_TYPE_IDS.items() if v is None]
    if missing:
        print(f"  WARNING: FK IDs not set for: {missing}")
        print(f"  Run discover_all.py first, then update ERROR_CODE_TYPE_IDS")
        print(f"  in error_code_mst_data.py. API calls will likely fail.")
        print()
        return False
    return True


def batch_create(client, count, dry_run=False, dropdown_ids=None):
    success = 0
    fail = 0
    types_used = []
    start = time.time()

    print("=" * 70)
    print(f"  ERROR CODE MST BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_error_code_mst_api_payload(dropdown_ids=dropdown_ids)
        code = payload.get("code", "?")
        type_ref = payload.get("error_code_type_ref_id")
        desc = payload.get("description", "")

        types_used.append(type_ref)

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {code:20s} | Type={type_ref} | {desc}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            rid = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {code:20s} | ID={rid} | {desc}")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {code:20s} | {desc}")
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:   {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:      {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  Type IDs:  {sorted(set(t for t in types_used if t is not None))}")
    print(f"  None IDs:  {types_used.count(None)} entries with missing FK IDs")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]
    dropdown_ids = args["dropdown_ids"]

    if not token:
        print("=" * 70)
        print("  ERROR CODE MST BATCH CREATE")
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

    # Check if FK IDs are populated
    _check_dropdown_ids()

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)

    result = client.list_entries("Error Code Mst", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run, dropdown_ids)
    client.close()


if __name__ == "__main__":
    main()
