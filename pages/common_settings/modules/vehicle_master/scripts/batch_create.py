#!/usr/bin/env python3
"""
Vehicle Master — Batch Create via API

Flat screen with 2 FK dropdowns (vehicle_type_id, fuel_type_ref_id).
Auto-discovers FK IDs via FkResolver at runtime.

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
from common.fk_resolver import FkResolver
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_vehicle_master_api_payloads,
    VEHICLE_TYPE_IDS,
    FUEL_TYPE_IDS,
)

SCREEN_NAME = "Vehicle Master"

FK_SCREEN_MAP = {
    "vehicle_type_id": "Vehicle Type",
    "fuel_type_ref_id": "Fuel Type",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Vehicle Master entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument("--offset", type=int, default=0, help="Start index in data pool")
    return parser.parse_args()


def resolve_all_fk_ids(resolver):
    """Resolve all Vehicle Master FK IDs from the live ERP."""
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
    count = args.count if args.count else 10

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {args.offset}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    # ── Generate payloads BEFORE token/auth (dry-run works without auth) ─
    print()
    print(f"  Generating {count} payloads (offset={args.offset})...")
    try:
        payloads = generate_vehicle_master_api_payloads(count=count, offset=args.offset, fk_ids={})
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        return

    # ── DRY RUN: print & exit (no token needed) ─────────────────────────
    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            name = f"name={p.get('name','')[:30]} vt={p.get('vehicle_type_id','')} ft={p.get('fuel_type_ref_id','')}"
            print(f"    [{j+1}] {name}")
        return

    # ── Only NOW ask for token ──────────────────────────────────────────
    args = prompt_missing_args(args)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs from live ERP...")
    resolver = FkResolver(api)
    fk_ids = resolve_all_fk_ids(resolver)

    # Try extra screen name variations if first attempt failed
    if "vehicle_type_id" not in fk_ids or not fk_ids["vehicle_type_id"]:
        for attempt in ["Vehicle Category", "Vehicle Master Type"]:
            resolved = resolver.resolve(attempt)
            if resolved:
                print(f"    vehicle_type_id: Found {len(resolved)} values from '{attempt}'")
                fk_ids["vehicle_type_id"] = resolved
                break

    if "fuel_type_ref_id" not in fk_ids or not fk_ids["fuel_type_ref_id"]:
        for attempt in ["Fuel Type Master", "Fuel Category"]:
            resolved = resolver.resolve(attempt)
            if resolved:
                print(f"    fuel_type_ref_id: Found {len(resolved)} values from '{attempt}'")
                fk_ids["fuel_type_ref_id"] = resolved
                break

    # ── Re-generate payloads with resolved FK IDs ─────────────────────
    print()
    print(f"  Re-generating {count} payloads with resolved FK IDs...")
    try:
        payloads = generate_vehicle_master_api_payloads(count=count, offset=args.offset, fk_ids=fk_ids)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    # ── Validate FK fields before sending ─────────────────────────────
    for i, p in enumerate(payloads):
        missing = []
        if p.get("vehicle_type_id") is None:
            missing.append("vehicle_type_id")
        if p.get("fuel_type_ref_id") is None:
            missing.append("fuel_type_ref_id")
        if missing:
            print(f"  WARNING: Payload {i+1} has None FK fields: {missing}")

    # ── Create entries ────────────────────────────────────────────────
    print()
    try:
        results = api.batch_create(SCREEN_NAME, payloads)
    except Exception as e:
        print(f"  ERROR: {e}")
        api.close()
        return

    # ── Summary ────────────────────────────────────────────────────────
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
