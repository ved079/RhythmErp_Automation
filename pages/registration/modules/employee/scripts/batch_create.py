#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Employee entries via API with randomized data.

The Employee screen is FLAT (no steppers), making batch creation
lightning-fast — ~0.2s per entry vs 30-60s via UI.

Usage:
    python pages/registration/modules/employee/scripts/batch_create.py
    python pages/registration/modules/employee/scripts/batch_create.py --count 20
    python pages/registration/modules/employee/scripts/batch_create.py --token eyJhbGci...
    python pages/registration/modules/employee/scripts/batch_create.py --dry-run --count 5
"""

import sys
import os
import time
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.employee.data.employee_data import (
    generate_employee_api_payload,
    DESIGNATION_NAMES,
)

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
    """Create multiple Employee entries and report stats.

    Args:
        client: Authenticated RhythmERPAPIClient instance.
        count: Number of Employee entries to create.
        dry_run: If True, generate payloads but don't POST.

    Returns:
        (success, fail) tuple with counts.
    """
    success = 0
    fail = 0
    designations_used = []
    start = time.time()

    print("=" * 70)
    print(f"  EMPLOYEE BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_employee_api_payload()
        name = payload['name']
        designation_id = payload.get('designation')
        designation_name = DESIGNATION_NAMES.get(designation_id, "?")
        designations_used.append(designation_name)

        if dry_run:
            print(f'  [{i+1:2d}] [DRY] {name:30s} | Designation={designation_name}')
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            print(f'  [{i+1:2d}] OK  {name:30s} | Designation={designation_name}')
            success += 1
        else:
            print(f'  [{i+1:2d}] FAIL {name:30s}')
            fail += 1

        time.sleep(0.2)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/max(count,1):.2f}s per entry)")
    # Show unique designations used
    unique_designations = sorted(set(designations_used))
    print(f"  Designations: {len(unique_designations)} unique — {unique_designations[:5]}{'...' if len(unique_designations) > 5 else ''}")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    # Dry-run doesn't need a token
    if dry_run:
        batch_create(None, count, dry_run=True)
        return

    if not token:
        print("=" * 70)
        print("  EMPLOYEE BATCH CREATE")
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
    result = client.list_entries("Employee", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
