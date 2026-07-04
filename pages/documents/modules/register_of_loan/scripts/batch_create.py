#!/usr/bin/env python3
"""
Register of Loan â€” Batch Create via API

Flat screen (no steppers) with 2 FK dropdowns (Facility Details, EMI Period)
that come from tbl_master (not dynamic screens â€” IDs are hardcoded).

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
from pages.documents.modules.register_of_loan.data.register_of_loan_data import (
    generate_batch_payloads,
    FACILITY_DETAILS_IDS,
    FACILITY_DETAILS_NAMES,
    EMI_PERIOD_IDS,
    EMI_PERIOD_NAMES,
)

SCREEN_NAME = "Register of Loan"

NOTE = (
    "  NOTE: FK dropdowns come from tbl_master (not dynamic screens).\n"
    "  Facility Details: CC(652), Term Loan(651), Non Funded(1547)\n"
    "  EMI Period: Monthly(1528), Quaterly(1529), Half Yearly(1530), Yearly(1531)"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Register of Loan entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument("--offset", type=int, default=0, help="Start index in data pool")
    parser.add_argument("--facility-details", type=int, default=None,
                        help="Override Facility Details FK ID for ALL entries")
    parser.add_argument("--emi-period", type=int, default=None,
                        help="Override EMI Period FK ID for ALL entries")
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

    overrides = {}
    if args.facility_details is not None:
        overrides["facility_details_ref_id"] = args.facility_details
        name = FACILITY_DETAILS_NAMES.get(args.facility_details, "?")
        print(f"  Facility Details overridden: {name} ({args.facility_details})")
    if args.emi_period is not None:
        overrides["emi_period"] = args.emi_period
        name = EMI_PERIOD_NAMES.get(args.emi_period, "?")
        print(f"  EMI Period overridden: {name} ({args.emi_period})")

    # â”€â”€ Generate payloads BEFORE token/auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print()
    print(f"  Generating {count} payloads (offset={args.offset})...")
    try:
        payloads = generate_batch_payloads(count=count, offset=args.offset, **overrides)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        return

    # â”€â”€ DRY RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            bank = p.get("bank_name", "?")[:30]
            san = p.get("sanction_amount", 0)
            print(f"    [{j+1}] Bank={bank}  Amt={san}")
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
