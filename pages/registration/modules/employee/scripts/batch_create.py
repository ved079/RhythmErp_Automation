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

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from pages.registration.modules.employee.data.employee_data import (
    generate_employee_api_payload,
)

DEFAULT_TENANT_ID = "599"
DEFAULT_COUNT = 10


def parse_args():
    """Parse simple --key value args from sys.argv."""
    args = {"token": None, "count": DEFAULT_COUNT, "dry_run": False, "tenant": DEFAULT_TENANT_ID}
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
    """Create multiple Employee entries and report stats.

    Args:
        client: Authenticated ErpApiClient instance.
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
        name = payload["name"]
        designation = payload.get("designation")
        designations_used.append(designation)

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {name:40s} | Desig={designation}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            entry_id = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {name:40s} | ID={entry_id} Desig={designation}")
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
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/max(count,1):.2f}s per entry)")
    print(f"  Designations:{sorted(set(designations_used))} ({len(set(designations_used))} unique)")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  EMPLOYEE BATCH CREATE")
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

    tenant_id = args.get("tenant", DEFAULT_TENANT_ID)
    client = ErpApiClient()
    client.set_session_from_token(token, tenant_id=tenant_id)

    result = client.list_entries("Employee", page=1, page_size=1)
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
