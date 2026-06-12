#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Farmer entries via API with randomized data.

⚠  KNOWN ERP BUG: Farmer creation via API POST currently returns HTTP 500
   with error "token has wrong type". This is a confirmed ERP-side bug —
   UI-only creation works correctly. This script attempts API creation
   anyway so it will work automatically once the bug is fixed.

Just paste your Bearer token and go.

Usage:
    python pages/registration/modules/farmer/scripts/batch_create.py
    python pages/registration/modules/farmer/scripts/batch_create.py --count 20
    python pages/registration/modules/farmer/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import time
import json

# Add project root to path (farmer/scripts → farmer → modules → registration → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.farmer.data.farmer_data import (
    generate_farmer_api_payload,
    generate_batch_payloads,
)
from pages.registration.modules.farmer.utils.api_farmer_utils import FarmerAPIUtils
from pages.registration.modules.farmer.utils.farmer_cleanup import CleanupTracker

# Default config — override with --token and --count flags
DEFAULT_TENANT_ID = "681"
DEFAULT_COUNT = 10

# Known ERP bug: Farmer creation via API POST returns 500 "token has wrong type"
ERP_BUG_MESSAGE = (
    "Known ERP bug: Farmer API creation returns HTTP 500 "
    "('token has wrong type'). UI creation works correctly. "
    "This script attempts API creation anyway for future compatibility."
)


def parse_args():
    """Parse simple --key value args from sys.argv."""
    args = {
        "token": None,
        "count": DEFAULT_COUNT,
        "dry_run": False,
        "tenant": DEFAULT_TENANT_ID,
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
        elif arg == "--tenant" and i + 1 < len(sys.argv):
            args["tenant"] = sys.argv[i + 1]
            i += 2
        elif arg == "--dry-run":
            args["dry_run"] = True
            i += 1
        else:
            i += 1
    return args


def batch_create(client, count, dry_run=False):
    """Create multiple Farmer entries and report stats.

    Args:
        client:  Authenticated RhythmERPAPIClient instance.
        count:   Number of Farmer entries to create.
        dry_run: If True, generate payloads but skip API calls.

    Returns:
        Tuple of (success_count, fail_count).
    """
    success = 0
    fail = 0
    http_500_count = 0
    states_used = []
    farmer_categories_used = []
    ownerships_used = []
    start = time.time()

    tracker = CleanupTracker()

    print("=" * 70)
    print(f"  FARMER BATCH CREATE — {count} entries")
    print("=" * 70)
    print(f"  ⚠  {ERP_BUG_MESSAGE}")
    print("=" * 70)

    for i in range(count):
        payload = generate_farmer_api_payload()

        # Extract key fields for reporting
        # Address Details: children[0] (Permanent + Current addresses)
        addr_details = payload['children'][0]['details']
        permanent_addr = next(
            (a for a in addr_details if a.get('address_type') == 1875),
            addr_details[0] if addr_details else {},
        )
        # Bank Details: children[2]
        bank = payload['children'][2]['details'][0] if payload['children'][2]['details'] else {}

        state = permanent_addr.get('state_ref_id_id')
        farmer_category = payload.get('farmer_category', [])
        ownership = payload.get('ownership_status_ref_id')
        name = payload.get('name', '?')

        states_used.append(state)
        farmer_categories_used.append(tuple(sorted(farmer_category)) if isinstance(farmer_category, list) else farmer_category)
        ownerships_used.append(ownership)

        if dry_run:
            print(f'  [{i+1:2d}] [DRY] {name:40s} | State={state:3d} Cat={farmer_category} Own={ownership}')
            success += 1
            continue

        result = client.create_entry(payload)

        if result:
            fid = result.get('id', '?')
            print(f'  [{i+1:2d}] OK  {name:40s} | ID={fid} State={state:3d} Own={ownership}')
            tracker.track(id=fid, company_name=name, payload_summary="Created via batch_create")
            success += 1
        else:
            # Check if failure was the known ERP 500 bug
            raw = client._last_raw_response
            is_500_bug = False
            if raw is not None and raw.status_code == 500:
                http_500_count += 1
                is_500_bug = True
                try:
                    body = raw.json() if raw.text else {}
                    err_msg = json.dumps(body)[:120]
                except Exception:
                    err_msg = raw.text[:120] if raw.text else ""
                print(f'  [{i+1:2d}] 500 {name:40s} | ERP bug: {err_msg}')
                log.warning(
                    f"[Farmer Batch] HTTP 500 for '{name}' — known ERP bug. "
                    f"Response: {err_msg}"
                )
            else:
                status = raw.status_code if raw is not None else "?"
                print(f'  [{i+1:2d}] FAIL {name:40s} | HTTP {status}')
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if http_500_count:
        print(f"  HTTP 500:    {http_500_count} (known ERP bug — 'token has wrong type')")
        print(f"  ⚠  {ERP_BUG_MESSAGE}")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  States:      {sorted({s for s in states_used if s is not None})} ({len({s for s in states_used if s is not None})} unique)")
    print(f"  Categories:  {sorted(set(farmer_categories_used))} ({len(set(farmer_categories_used))} unique)")
    print(f"  Ownership:   {sorted({o for o in ownerships_used if o is not None})} ({len({o for o in ownerships_used if o is not None})} unique)")
    print("=" * 70)

    # Generate cleanup report for any successfully created entries
    if tracker.count > 0:
        report_paths = tracker.generate_reports()
        if report_paths:
            print()
            print("  Cleanup reports generated:")
            for fmt, path in report_paths.items():
                print(f"    {fmt}: {path}")
            print("  (No delete endpoint exists — use reports for manual DB purge)")
            print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  FARMER BATCH CREATE")
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

    tenant_id = args.get("tenant", DEFAULT_TENANT_ID)
    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=tenant_id)

    # Quick auth check
    result = client.list_entries("Farmer", page=1, page_size=1)
    if not result:
        raw = client._last_raw_response
        if raw is not None:
            status = raw.status_code
            body = raw.text[:300]
            print()
            print(f"  API error: {status} — {body}")
            print()
            if "Tenant not found" in body or status == 404:
                print(f"  !! Tenant ID '{tenant_id}' does NOT exist in the ERP database.")
                print("     Fix: Open DevTools -> Network -> click any /core/ request")
                print("     -> copy the X-Tenant-ID header value -> re-run with --tenant <id>")
                print()
                print(f"     Example:  python batch_create.py --tenant <correct_id>")
            elif "tenant access" in body.lower() or status == 403:
                print(f"  !! Tenant ID '{tenant_id}' exists but your user has NO ACCESS to it.")
                print("     Fix: Switch to a tenant your user belongs to,")
                print("     or ask an admin to grant access.")
            elif status == 401:
                print("  !! Token expired or invalid. Get a fresh one from DevTools.")
            else:
                print("  Check the error above and fix accordingly.")
        else:
            print()
            print("  API error: No response received (network issue or ERP unreachable).")
            print("  Check your internet connection and that the ERP is up.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
