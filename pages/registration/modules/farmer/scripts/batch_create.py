#/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple Farmer entries via API with randomized data.

KNOWN ERP BUG: Farmer creation via API POST currently returns HTTP 500
with error "token has wrong type". This is a confirmed ERP-side bug UI-only creation works correctly.

Usage:
    python pages/registration/modules/farmer/scripts/batch_create.py --token <jwt> --tenant <id> --count <n>
    python pages/registration/modules/farmer/scripts/batch_create.py --token eyJhbGci... --tenant 711 --count 10
"""

import sys
import os
import argparse
import time
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.fk_resolver import FkResolver
from pages.registration.modules.farmer.data.farmer_data import generate_farmer_api_payload
from pages.registration.modules.farmer.utils.farmer_cleanup import CleanupTracker


SCREEN_NAME = "Farmer"

# Fallback hardcoded IDs (tenant 681) — used only if live resolution fails
FARMER_CATEGORY_FALLBACKS = {
    "fpc":      [1593],
    "walkin":   [1592],
    "borrower": [1594],
}

# Label lookup for live resolution
FARMER_TYPE_LABELS = {
    "fpc":      "FPC Member",
    "walkin":   "Walk-in Farmer",
    "borrower": "Borrower Farmer",
}

ERP_BUG_MESSAGE = (
    "Known ERP bug: Farmer API creation returns HTTP 500 "
    "('token has wrong type'). UI creation works correctly. "
    "This script attempts API creation anyway for future compatibility."
)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Farmer entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument(
        "--farmer-type",
        choices=["fpc", "walkin", "borrower"],
        default="fpc",
        help="Farmer category type: fpc (FPC Member), walkin (Walk-in Farmer), borrower (Borrower Farmer). Default: fpc",
    )
    return parser.parse_args()


def batch_create(client, count, farmer_type="fpc", dry_run=False):
    success = 0
    fail = 0
    http_500_count = 0
    states_used = []
    farmer_categories_used = []
    ownerships_used = []
    start = time.time()

    tracker = CleanupTracker()

    type_label = FARMER_TYPE_LABELS[farmer_type]
    fallback_ids = FARMER_CATEGORY_FALLBACKS[farmer_type]

    # Resolve farmer category ID from live ERP by label
    print(f"  Resolving Farmer Category '{type_label}' from live ERP...")
    resolver = FkResolver(client)
    category_options = resolver.resolve("Farmer Category")
    fallback_id = FARMER_CATEGORY_FALLBACKS[farmer_type][0]
    if category_options:
        label_lower = type_label.strip().lower()
        matched_id = next(
            (int(fid) for name, fid in category_options.items()
             if str(name).strip().lower() == label_lower),
            None,
        )
        if matched_id:
            role_ids = matched_id
            print(f"  Resolved: '{type_label}' = {matched_id}")
        else:
            role_ids = fallback_id
            print(f"  WARNING: '{type_label}' not found in options {list(category_options.keys())}")
            print(f"  Falling back to hardcoded ID: {fallback_id}")
    else:
        role_ids = fallback_id
        print(f"  WARNING: Could not resolve Farmer Category — falling back to {fallback_id}")

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE -- {count} entries")
    print(f"  Type: {type_label} (role={role_ids})")
    print("=" * 70)

    for i in range(count):
        payload = generate_farmer_api_payload(dropdown_ids={"farmer_category": role_ids})

        addr_details = payload['children'][0]['details']
        permanent_addr = next(
            (a for a in addr_details if a.get('address_type') == 1875),
            addr_details[0] if addr_details else {},
        )
        bank_stepper = next((c for c in payload['children'] if c.get('stepper_name') == 'Bank Details'), {})
        bank = bank_stepper.get('details', [{}])[0] if bank_stepper.get('details') else {}

        state = permanent_addr.get('state_ref_id_id')
        farmer_category = payload.get('role', [])
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
        print(f"  HTTP 500:    {http_500_count} (known ERP bug -- 'token has wrong type')")
        print(f"  {ERP_BUG_MESSAGE}")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print(f"  States:      {sorted({s for s in states_used if s is not None})} ({len({s for s in states_used if s is not None})} unique)")
    print(f"  Categories:  {sorted(set(farmer_categories_used))} ({len(set(farmer_categories_used))} unique)")
    print(f"  Ownership:   {sorted({o for o in ownerships_used if o is not None})} ({len({o for o in ownerships_used if o is not None})} unique)")
    print("=" * 70)

    if tracker.count > 0:
        report_paths = tracker.generate_reports()
        if report_paths:
            print()
            print("  Cleanup reports generated:")
            for fmt, path in report_paths.items():
                print(f"    {fmt}: {path}")
            print("  (No delete endpoint exists -- use reports for manual DB purge)")
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

    batch_create(client, args.count, args.farmer_type, args.dry_run)
    client.close()


if __name__ == "__main__":
    main()
