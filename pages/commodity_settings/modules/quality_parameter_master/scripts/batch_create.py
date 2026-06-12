#!/usr/bin/env python3
"""
Quality Parameter Master — Batch Create

Creates quality parameter entries via the ERP API.

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --offset 20  # Skip first 20 in data pool

Screen structure:
  Quality Parameter Master: name* (text, required, unique)
  FLAT screen — no steppers, no children, no FK fields.
"""

import sys
import os
import argparse

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from pages.commodity_settings.modules.quality_parameter_master.data.quality_parameter_master_data import (
    generate_quality_parameter_payloads,
    QUALITY_PARAMETER_DATA,
)

SCREEN_NAME = "Quality Parameter Master"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Quality Parameter Master entries")
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of entries to create (omit to prompt)"
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Start index in data pool (to skip already-used names). Default: 0"
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


def main():
    args = parse_args()
    count = args.count if args.count else 10
    offset = args.offset

    print("=" * 70)
    print(f"  QUALITY PARAMETER MASTER — BATCH CREATE")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(QUALITY_PARAMETER_DATA)}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    try:
        payloads = generate_quality_parameter_payloads(count=count, offset=offset)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        return

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            print(f"    [{j+1}] name={p.get('name','')[:40]}")
        return

    args = prompt_missing_args(args)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

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
