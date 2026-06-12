#!/usr/bin/env python3
"""
HSN SAC — Batch Create

Screen: "HSN SAC" (flat, 1 dropdown: hsn_sac_type)
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
from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    generate_hsn_sac_api_payloads,
)

SCREEN_NAME = "HSN SAC"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create HSN SAC entries via API")
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
    args = prompt_missing_args(args)
    count = args.count

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs...")
    resolver = FkResolver(api)

    hsn_type_ids = {}
    for screen_attempt in ["HSN SAC Type", "HSN Type", "SAC Type", "HSN/SAC Type"]:
        hsn_type_ids = resolver.resolve(screen_attempt)
        if hsn_type_ids:
            print(f"    hsn_sac_type: Found {len(hsn_type_ids)} values from '{screen_attempt}'")
            break

    if not hsn_type_ids:
        print("    hsn_sac_type: NOT FOUND — will use fallback")

    fk_ids = {"hsn_sac_type": hsn_type_ids}

    # ── Generate payloads ─────────────────────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_hsn_sac_api_payloads(count=count, fk_ids=fk_ids)

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            print(f"    [{j+1}] code={p.get('hsn_sac_no','')} type={p.get('hsn_sac_type')} desc={p.get('hsn_sac_description','')[:30]}")
        api.close()
        return

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
