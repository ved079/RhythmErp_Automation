#!/usr/bin/env python3
"""
Tax Rate — Batch Create via API

Complex screen with stepper "Define Tax Rate Details".
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
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    generate_tax_rate_api_payloads,
    get_fk_screen_mapping,
    HSN_SAC_CODES,
)

SCREEN_NAME = "Tax Rate"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Tax Rate entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument("--offset", type=int, default=0, help="Start index in data pool")
    return parser.parse_args()


def get_fk_map():
    """Convert get_fk_screen_mapping() output to {field: screen_name} dict."""
    return {m["fk_field"]: m["screen_name"] for m in get_fk_screen_mapping()}

def resolve_all_fk_ids(resolver):
    """Resolve all Tax Rate FK IDs from the live ERP."""
    fk_map = get_fk_map()
    fk_ids = {}
    for field, screen in fk_map.items():
        try:
            resolved = resolver.resolve(screen)
            if resolved:
                print(f"    {field}: {len(resolved)} options found from '{screen}'")
                samples = list(resolved.items())[:3]
                for name, fid in samples:
                    print(f"      {name}: {fid}")
                fk_ids[field] = resolved
            else:
                print(f"    {field}: NOT FOUND")
        except Exception as e:
            print(f"    {field}: ERROR — {e}")
    # Try extra screen name variations for hsn_sac_number if needed
    if "hsn_sac_number" not in fk_ids or not fk_ids["hsn_sac_number"]:
        for attempt in ["HSN SAC Number", "HSN/SAC Number", "HSN SAC"]:
            resolved = resolver.resolve(attempt)
            if resolved:
                print(f"    hsn_sac_number: Found {len(resolved)} values from '{attempt}'")
                fk_ids["hsn_sac_number"] = resolved
                break
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

    # ── DRY RUN: just show what would be created (no auth needed) ────────
    if args.dry_run:
        print(f"  [DRY-RUN] Would create {count} Tax Rate entries (offset={args.offset})")
        print("  Skipping payload generation (requires resolved FK IDs).")
        print("  Run without --dry-run to resolve FK IDs and create entries.")
        return

    # ── Prompt for auth ────────────────────────────────────────────────
    args = prompt_missing_args(args)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs from live ERP...")
    resolver = FkResolver(api)
    fk_ids = resolve_all_fk_ids(resolver)

    if not fk_ids or not any(fk_ids.values()):
        print("  ERROR: Could not resolve any FK IDs. Cannot generate payloads.")
        api.close()
        return

    # ── Generate payloads with resolved FK IDs ────────────────────────
    print()
    print(f"  Generating {count} payloads with resolved FK IDs...")
    try:
        payloads = generate_tax_rate_api_payloads(count=count, offset=args.offset, fk_ids=fk_ids)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    # ── Validate FK fields before sending ─────────────────────────────
    for i, p in enumerate(payloads):
        missing = []
        if p.get("tax_type_ref_id") is None:
            missing.append("tax_type_ref_id")
        if p.get("tax_authority_ref_id") is None:
            missing.append("tax_authority_ref_id")
        # Check detail lines for hsn_sac_number FK
        children = p.get("children", [])
        for ci, child in enumerate(children):
            details = child.get("details", [])
            for di, detail in enumerate(details):
                if detail.get("hsn_sac_number") is None:
                    missing.append(f"children[{ci}].details[{di}].hsn_sac_number")
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
