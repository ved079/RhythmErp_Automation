#/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Customer entries via API with randomized data.

Usage:
    python pages/registration/modules/customer/scripts/batch_create.py --token <jwt> --tenant <id> --count <n>
    python pages/registration/modules/customer/scripts/batch_create.py --token eyJhbGci... --tenant 711 --count 10
"""

import sys
import os
import argparse
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.customer.data.customer_data import generate_customer_api_payload


SCREEN_NAME = "Customer"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Customer entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    return parser.parse_args()


def batch_create(client, count, dry_run=False):
    success = 0
    fail = 0
    states_used = []
    sale_types_used = []
    supply_types_used = []
    start = time.time()

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE -- {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_customer_api_payload()
        name = payload.get("name", "")
        state = payload.get("state")
        sale_type = payload.get("sale_type")
        supply_type = payload.get("supply_type")

        states_used.append(state)
        sale_types_used.append(sale_type)
        supply_types_used.append(supply_type)

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {name:40s} | State={state} Sale={sale_type} Supply={supply_type}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            cid = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {name:40s} | ID={cid} State={state} Sale={sale_type} Supply={supply_type}")
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
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  States:      {sorted(set(states_used))} ({len(set(states_used))} unique)")
    print(f"  Sale types:  {sorted(set(sale_types_used))} ({len(set(sale_types_used))} unique)")
    print(f"  Supply types:{sorted(set(supply_types_used))} ({len(set(supply_types_used))} unique)")
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
