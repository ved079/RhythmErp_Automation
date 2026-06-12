#!/usr/bin/env python3
"""
Services Master — Batch Create via API

Creates service master entries via the ERP API (bypasses the UI entirely).
Handles FK dropdown fields (UOM, Base UOM, HSN SAC Code) using ID maps.

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --offset 20  # Skip first 20 in data pool

Screen structure:
  Services Master: name* (text), uom* (FK→UOM), base_uom* (FK→UOM),
                   base_uom_conversion* (text), hsn_code* (FK→HSN SAC Services),
                   status (toggle)
  FLAT screen — no steppers, no children.
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
from pages.commodity_settings.modules.services_master.data.services_master_data import (
    generate_services_master_payloads,
    SERVICES_MASTER_API_DATA,
)

SCREEN_NAME = "Services Master"

# FK fields that need resolution from live ERP
FK_SCREEN_MAP = {
    "uom": "UOM",
    "hsn_code": "HSN SAC",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Services Master entries via API")
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


def resolve_all_fk_ids(resolver):
    """Resolve all Services Master FK IDs from the live ERP."""
    fk_ids = {}
    for field, screen in FK_SCREEN_MAP.items():
        try:
            resolved = resolver.resolve(screen)
            if resolved:
                print(f"    {field}: {len(resolved)} options found from '{screen}'")
                samples = list(resolved.items())[:3]
                for name, fid in samples:
                    print(f"      {name}: {fid}")
                fk_ids[field] = resolved
            else:
                print(f"    {field}: NOT FOUND — will fall back to hardcoded IDs")
        except Exception as e:
            print(f"    {field}: ERROR — {e}")
    return fk_ids


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
    offset = args.offset

    print("=" * 70)
    print(f"  SERVICES MASTER — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(SERVICES_MASTER_API_DATA)}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs from live ERP...")
    resolver = FkResolver(api)
    fk_ids = resolve_all_fk_ids(resolver)

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    try:
        payloads = generate_services_master_payloads(count=count, offset=offset, fk_ids=fk_ids)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            missing = []
            for fk in ["uom", "base_uom", "hsn_code"]:
                if p.get(fk) is None:
                    missing.append(fk)
            flag = " !! MISSING FKs: " + ",".join(missing) if missing else ""
            print(f"    [{j+1}] name={p.get('name','')[:30]} uom={p.get('uom')} base_uom={p.get('base_uom')} hsn={p.get('hsn_code')}{flag}")
        api.close()
        return

    # Validate FK fields before sending
    for i, p in enumerate(payloads):
        missing = []
        for fk_field in ["uom", "base_uom", "hsn_code"]:
            if p.get(fk_field) is None:
                missing.append(fk_field)
        if missing:
            print(f"  WARNING: Payload {i+1} has None FK fields: {missing}")

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


if __name__ == "__main__":
    main()
