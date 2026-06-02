#!/usr/bin/env python3
"""
Commodity Quality Parameter — Batch Create via API

Creates CQP entries via the ERP API (bypasses the UI entirely).
Handles FK dropdown fields (Item Name, Transaction Type, Quality Parameter)
and properly creates detail rows inside the stepper grid.

IMPORTANT — Unique Constraint:
  The ERP enforces uniqueness on (item_ref_id, to_date). Each item can only
  have ONE CQP entry per to_date value. The data pool uses items that are
  NOT already present in CQP with the default to_date=2099-12-30T18:30:00Z.

Payload Structure (stepper with grid detail):
  {
    "id": "",
    "attribute_name": "Commodity Quality Parameter",
    "item_ref_id": <int>,          // FK → Item Master
    "transaction_type": <int>,     // FK → Transaction Type options
    "from_date": "<ISO datetime>", // Auto-set by server on create
    "to_date": "2099-12-30T18:30:00Z",
    "revision_status": "<str or null>",
    "details": [],
    "children": [
      {
        "stepper_name": "Define Item Quality Parameter Details",
        "is_stepper": true,
        "details": [                  <--- Quality param detail rows go here
          {
            "quality_type": <int>,    // FK → Quality Parameter
            "min_quality_value": "<str>",
            "max_quality_value": "<str>",
            "rate_percentage": <bool>,
            "multiplier": "<str>"
          }
        ],
        "children": []
      }
    ]
  }

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --offset 10  # Skip first 10 in data pool

Screen: Commodity Quality Parameter
URL:    /#/dynamic-screens/Commodity%20Quality%20Parameter
"""

import sys
import os
import argparse

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    generate_cqp_payloads,
    COMMODITY_QUALITY_PARAMETER_API_DATA,
    ITEM_ID_MAP,
    TRANSACTION_TYPE_ID_MAP,
    QUALITY_PARAM_ID_MAP,
    CQP_USED_ITEM_IDS,
)

SCREEN_NAME = "Commodity Quality Parameter"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Commodity Quality Parameter entries via API")
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
    print(f"  COMMODITY QUALITY PARAMETER — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(COMMODITY_QUALITY_PARAMETER_API_DATA)}")
    print(f"  Item IDs mapped: {len(ITEM_ID_MAP)}")
    print(f"  Transaction Type IDs: {len(TRANSACTION_TYPE_ID_MAP)}")
    print(f"  Quality Param IDs: {len(QUALITY_PARAM_ID_MAP)}")
    print(f"  Already-used item IDs (skip): {len(CQP_USED_ITEM_IDS)}")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Generate payloads ─────────────────────────────────────────────
    try:
        payloads = generate_cqp_payloads(count=count, offset=offset)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    # Validate FK fields before sending
    for i, p in enumerate(payloads):
        missing = []
        if p.get("item_ref_id") is None:
            missing.append("item_ref_id")
        if p.get("transaction_type") is None:
            missing.append("transaction_type")
        # Check detail rows
        stepper = p.get("children", [{}])[0] if p.get("children") else {}
        detail_rows = stepper.get("details", [])
        for j, row in enumerate(detail_rows):
            if row.get("quality_type") is None:
                missing.append(f"detail[{j}].quality_type")
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

    # Show details for failed entries
    if failed > 0:
        for i, r in enumerate(results):
            if not r.get("success"):
                entry_info = ""
                if i < len(payloads):
                    p = payloads[i]
                    item_id = p.get("item_ref_id", "?")
                    entry_info = f" (item_ref_id={item_id})"
                print(f"  FAILED entry {i+1}{entry_info}: {r.get('error', 'Unknown')}")

    print(f"  Total: {created} created, {failed} failed out of {count}")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()
