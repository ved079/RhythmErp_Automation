#!/usr/bin/env python3
"""
Item Master — Batch Create via API

Creates item master entries via the ERP API (bypasses the UI entirely).
Handles the 3-step stepper payload structure with children arrays.

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 1    # Creates 1 entry
    python batch_create.py --dry-run    # Preview payloads without sending

Screen structure:
  Item Master: 3-step stepper form
    Step 1 - Additional Details: 15 fields + 4 toggles
    Step 2 - Define Item Master Details: Attachment only
    Step 3 - Product Order Packaging Details: Grid table
"""

import sys
import os
import argparse

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from pages.commodity_settings.modules.item_master.data.item_master_data import (
    generate_item_master_payloads,
    ITEM_MASTER_DATA_POOL,
)

SCREEN_NAME = "Item Master"

# Map FK field to the screen name used in FkResolver
FK_SCREEN_MAP = {
    "item_category":   "Item Category",
    "item_group":      "Item Group",
    "item_type":       "Item Type",
    "item_attribute1": "Item Attribute1",
    "item_attribute2": "Item Attribute2",
    "item_attribute3": "Item Attribute3",
    "item_attribute4": "Item Attribute4",
    "item_attribute5": "Item Attribute5",
    "uom":             "UOM",
    "base_uom":        "UOM",
    "hsn_sac_code":    "HSN SAC",
    "sourcing_type":   "Item Sourcing",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Item Master entries via API")
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of entries to create (omit to prompt)"
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Start index in data pool (to skip already-used entries). Default: 0"
    )
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
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


def resolve_all_fk_ids(resolver):
    """Resolve all Item Master FK IDs from the live ERP."""
    fk_ids = {}
    for field, screen in FK_SCREEN_MAP.items():
        try:
            resolved = resolver.resolve(screen)
            if resolved:
                print(f"    {field}: {len(resolved)} options found")
                # Show first 3 sample values
                samples = list(resolved.items())[:3]
                for name, fid in samples:
                    print(f"      {name}: {fid}")
                fk_ids[field] = resolved
            else:
                print(f"    {field}: NOT FOUND — will fall back to hardcoded IDs")
        except Exception as e:
            print(f"    {field}: ERROR — {e}")
    return fk_ids


def main():
    args = parse_args()

    if not args.dry_run:
        args = prompt_missing_args(args)
    count = args.count if args.count else 10
    offset = args.offset

    print("=" * 70)
    print(f"  ITEM MASTER — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(ITEM_MASTER_DATA_POOL)}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    api = ErpApiClient()
    fk_ids = {}

    if not args.dry_run:
        api.set_session_from_token(args.token, tenant_id=args.tenant)

    if not args.dry_run:
        # ── Resolve FK IDs ────────────────────────────────────────────
        print()
        print("  Resolving FK IDs from live ERP...")
        resolver = FkResolver(api)
        fk_ids = resolve_all_fk_ids(resolver)

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    try:
        payloads = generate_item_master_payloads(count=count, offset=offset, fk_ids=fk_ids)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        if api:
            api.close()
        return

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            print(f"    [{j+1}] name={p.get('name','')[:60]} cat={p.get('item_category')} type={p.get('item_type')} uom={p.get('uom')} base_uom={p.get('base_uom')} hsn={p.get('hsn_sac_code')} src={p.get('sourcing_type')} desc={p.get('description','')[:30]}")
        api.close()
        return

    # ── Create entries ────────────────────────────────────────────────
    print()
    print(f"  Creating {count} entries on '{SCREEN_NAME}'...")
    print("-" * 70)

    try:
        results = api.batch_create(SCREEN_NAME, payloads)
    except Exception as e:
        print(f"  ERROR: {e}")
        api.close()
        return

    # ── Summary ───────────────────────────────────────────────────────
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
