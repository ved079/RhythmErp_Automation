#!/usr/bin/env python3
"""
Register Charges â€” Batch Create via API

Flat screen (no steppers) with 1 FK dropdown (Type of Charge)
that comes from tbl_master (not a dynamic screen â€” IDs are hardcoded).

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --dry-run    # Preview payloads without sending
"""

import sys
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from pages.documents.modules.register_charges.data.register_charges_data import (
    generate_batch_payloads,
    TYPE_OF_CHARGE_IDS,
    TYPE_OF_CHARGE_NAMES,
)

SCREEN_NAME = "Register Charges"

NOTE = (
    "  NOTE: type_of_charge_ref_id comes from tbl_master (not a dynamic screen).\n"
    "  IDs are hardcoded but can be overridden via --type-of-charge.\n"
    "  Options: Mortgage(1909), Hypothecation(1910), Pledge(1911)"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Register Charges entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument("--offset", type=int, default=0, help="Start index in data pool")
    parser.add_argument("--type-of-charge", type=int, default=None,
                        help="Override Type of Charge FK ID for ALL entries")
    return parser.parse_args()


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
    count = args.count if args.count else 10

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} â€” BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {args.offset}")
    print(NOTE)
    if args.dry_run:
        print("  ** DRY-RUN MODE â€” no entries will be created **")
    print("=" * 70)

    # Build overrides
    overrides = {}
    if args.type_of_charge is not None:
        overrides["type_of_charge_ref_id"] = args.type_of_charge
        name = TYPE_OF_CHARGE_NAMES.get(args.type_of_charge, "?")
        print(f"  Type of Charge overridden: {name} ({args.type_of_charge})")

    # â”€â”€ Generate payloads BEFORE token/auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print()
    print(f"  Generating {count} payloads (offset={args.offset})...")
    try:
        payloads = generate_batch_payloads(count=count, offset=args.offset, **overrides)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        return

    # â”€â”€ DRY RUN: print & exit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            roc = p.get("roc_charge_id", "?")
            toc_id = p.get("type_of_charge_ref_id", "?")
            toc_name = TYPE_OF_CHARGE_NAMES.get(toc_id, str(toc_id))
            amt = p.get("amount_secured", 0)
            print(f"    [{j+1}] ROC={roc}  Type={toc_name}  Amt={amt}")
        return

    # â”€â”€ Only NOW ask for token â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    args = prompt_missing_args(args)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # â”€â”€ Create entries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print()
    try:
        results = api.batch_create(SCREEN_NAME, payloads)
    except Exception as e:
        print(f"  ERROR: {e}")
        api.close()
        return

    # â”€â”€ Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    created = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))

    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    status_icon = "OK" if failed == 0 else "!!"
    print(f"  [{status_icon}] {SCREEN_NAME:<35} {created:>3}/{count} created")
    print("-" * 70)
    print(f"  Total: {created} created, {failed} failed out of {count}")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()
