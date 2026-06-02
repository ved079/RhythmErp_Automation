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
from pages.commodity_settings.modules.services_master.data.services_master_data import (
    generate_services_master_payloads,
    SERVICES_MASTER_API_DATA,
    UOM_ID_MAP,
    HSN_SAC_SERVICES_ID_MAP,
)

SCREEN_NAME = "Services Master"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Services Master entries via API")
    parser.add_argument(
        "--count", type=int, default=10,
        help="Number of entries to create. Default: 10"
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Start index in data pool (to skip already-used entries). Default: 0"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    count = args.count
    offset = args.offset

    print("=" * 70)
    print(f"  SERVICES MASTER — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(SERVICES_MASTER_API_DATA)}")
    print(f"  UOM IDs: {len(UOM_ID_MAP)} mapped")
    print(f"  HSN SAC IDs: {len(HSN_SAC_SERVICES_ID_MAP)} mapped")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Generate payloads ─────────────────────────────────────────────
    try:
        payloads = generate_services_master_payloads(count=count, offset=offset)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
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
            entry = SERVICES_MASTER_API_DATA[(offset + i) % len(SERVICES_MASTER_API_DATA)]
            print(f"    Data pool entry: {entry}")

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
