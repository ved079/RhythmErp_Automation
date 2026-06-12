#!/usr/bin/env python3
"""
UOM Conversion — Batch Create

Screen: "UOM Conversion" (flat, 2 FK dropdowns: source_uom_code, target_uom_code)
Auto-discovers FK IDs at startup (both use UOM screen).
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
from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_api_payloads,
)

SCREEN_NAME = "UOM Conversion"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create UOM Conversion entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
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

    if not args.dry_run:
        args = prompt_missing_args(args)
    count = args.count if args.count else 10

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    api = ErpApiClient()
    fk_ids = {}

    if not args.dry_run:
        api.set_session_from_token(args.token, tenant_id=args.tenant)

        # ── Resolve FK IDs ────────────────────────────────────────────
        print()
        print("  Resolving FK IDs...")
        resolver = FkResolver(api)

        uom_ids = resolver.resolve("UOM")
        print(f"    UOM IDs: {len(uom_ids)} found")

        uom_code_ids = resolver.resolve("UOM Code")
        if uom_code_ids and len(uom_code_ids) > len(uom_ids):
            uom_ids = uom_code_ids
            print(f"    UOM Code IDs: {len(uom_code_ids)} found (using these — better match)")

        if uom_ids:
            sample = list(uom_ids.items())[:5]
            for name, uid in sample:
                print(f"      {name}: {uid}")
            if len(uom_ids) > 5:
                print(f"      ... and {len(uom_ids) - 5} more")

        fk_ids = {
            "source_uom_code": uom_ids,
            "target_uom_code": uom_ids,
        }

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_uom_conversion_api_payloads(count=count, fk_ids=fk_ids)

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            print(f"    [{j+1}] {p.get('source_uom_code')} -> {p.get('target_uom_code')} = {p.get('conversion_factor')}")
    else:
        # ── Batch create ──────────────────────────────────────────────
        print()
        print("=" * 70)
        print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
        print("=" * 70)

        results = api.batch_create(SCREEN_NAME, payloads)
        api.print_results(results, SCREEN_NAME)

    api.close()


if __name__ == "__main__":
    main()
