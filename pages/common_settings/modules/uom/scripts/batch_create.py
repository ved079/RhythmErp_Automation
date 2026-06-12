#!/usr/bin/env python3
"""
batch_create.py
---------------
Create multiple UOM entries via API with realistic measurement unit codes.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/uom/scripts/batch_create.py
    python pages/common_settings/modules/uom/scripts/batch_create.py --count 20
    python pages/common_settings/modules/uom/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import argparse
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.uom.data.uom_data import generate_uom_api_payload


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create UOM entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    return parser.parse_args()


def batch_create(client, count, dry_run=False):
    success = 0
    fail = 0
    start = time.time()

    print("=" * 70)
    print(f"  UOM BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_uom_api_payload()
        code = payload.get("uom_code", "?")
        desc = payload.get("uom_description", "")

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {code:8s} — {desc}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            rid = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {code:8s} — {desc:30s} | ID={rid}")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {code:8s} — {desc}")
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created: {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:    {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
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

    result = client.list_entries("UOM", page=1, page_size=1)
    if not result:
        raw = client._last_raw_response
        if raw is not None:
            status = raw.status_code
            body = raw.text[:300]
            print()
            print(f"  API error: {status} — {body}")
            print()
            if "Tenant not found" in body or status == 404:
                print(f"  !! Tenant ID '{args.tenant}' does NOT exist in the ERP database.")
            elif "tenant access" in body.lower() or status == 403:
                print(f"  !! Tenant ID '{args.tenant}' exists but your user has NO ACCESS to it.")
            elif status == 401:
                print("  !! Token expired or invalid. Get a fresh one from DevTools.")
            else:
                print("  Check the error above and fix accordingly.")
        else:
            print()
            print("  API error: No response received (network issue or ERP unreachable).")
        client.close()
        return

    batch_create(client, args.count, args.dry_run)
    client.close()


if __name__ == "__main__":
    main()
