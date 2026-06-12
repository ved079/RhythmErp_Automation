#!/usr/bin/env python3
"""
Bank — Batch Create

Screen: "Bank" (flat, 2 FK dropdowns: account_type, account_ref_id)
Auto-discovers FK IDs at startup.
"""

import sys
import os
import argparse
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from pages.common_settings.modules.bank.data.bank_data import (
    generate_bank_api_payloads,
)

SCREEN_NAME = "Bank"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Bank entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
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
    args = prompt_missing_args(args)
    count = args.count

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
    print("=" * 70)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs...")
    resolver = FkResolver(api)

    # Account Type
    at_ids = resolver.resolve("Account Type")
    print(f"    account_type: {len(at_ids)} Account Types found")

    # Account Reference — try multiple names
    ar_ids = {}
    for attempt in ["Account", "Chart of Account", "Account Reference", "Account Ref", "Ledger"]:
        ar_ids = resolver.resolve(attempt)
        if ar_ids:
            print(f"    account_ref_id: Found {len(ar_ids)} values from '{attempt}'")
            break
    if not ar_ids:
        print("    account_ref_id: NOT FOUND — will omit from payload (optional field)")

    fk_ids = {
        "account_type": at_ids,
        "account_ref_id": ar_ids,
    }

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_bank_api_payloads(count=count, fk_ids=fk_ids)

    # ── Batch create ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
    print("=" * 70)

    results = api.batch_create(SCREEN_NAME, payloads)
    api.print_results(results, SCREEN_NAME)
    api.close()


if __name__ == "__main__":
    main()
