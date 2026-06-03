#!/usr/bin/env python3
"""
Item Attribute — Generic Batch Create

Works for ANY Item Attribute screen (1-5). Run with:
    python batch_create.py              # Creates all 5 attributes (10 each)
    python batch_create.py --attr 1     # Only Item Attribute1
    python batch_create.py --attr 1,2,3 # Attributes 1, 2, and 3
    python batch_create.py --count 20   # 20 entries per screen instead of 10

Screen structures:
  Item Attribute1: name*, base_uom* (FK→UOM), description, status
  Item Attribute2-5: name*, description, status
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
from pages.commodity_settings.modules.item_attribute.data.item_attribute_data import (
    generate_item_attribute_payloads,
    ATTRIBUTE_POOLS,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Item Attribute entries")
    parser.add_argument(
        "--attr", type=str, default="1,2,3,4,5",
        help="Comma-separated attribute numbers (1-5). Default: all 5"
    )
    parser.add_argument(
        "--count", type=int, default=10,
        help="Number of entries per screen. Default: 10"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Parse attribute numbers
    try:
        attr_numbers = [int(x.strip()) for x in args.attr.split(",")]
    except ValueError:
        print("  Error: --attr must be comma-separated numbers (e.g., 1,2,3)")
        return

    for n in attr_numbers:
        if n not in ATTRIBUTE_POOLS:
            print(f"  Error: Invalid attribute number {n}. Must be 1-5.")
            return

    count = args.count

    print("=" * 70)
    print(f"  ITEM ATTRIBUTE BATCH CREATE")
    print(f"  Attributes: {[f'Item Attribute{n}' for n in attr_numbers]}")
    print(f"  Count per screen: {count}")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Resolve FK IDs for Item Attribute1 (needs base_uom) ──────────
    resolver = FkResolver(api)
    fk_ids = {}

    if 1 in attr_numbers:
        uom_ids = resolver.resolve("UOM")
        if uom_ids:
            print(f"    base_uom: {len(uom_ids)} UOMs found")
        else:
            print(f"    base_uom: Using hardcoded UOM IDs")
        fk_ids["base_uom"] = uom_ids

    # ── Create entries for each attribute ─────────────────────────────
    all_results = {}

    for attr_number in attr_numbers:
        screen_name = f"Item Attribute{attr_number}"
        label = ATTRIBUTE_POOLS[attr_number][0]

        print()
        print(f"  ── {screen_name} ({label}) ──")
        print("-" * 70)

        try:
            payloads = generate_item_attribute_payloads(
                attr_number=attr_number,
                count=count,
                fk_ids=fk_ids,
            )
            results = api.batch_create(screen_name, payloads)
            all_results[attr_number] = results

            created = sum(1 for r in results if r.get("success"))
            failed = sum(1 for r in results if not r.get("success"))
            print(f"  Result: {created}/{count} created, {failed} failed")

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[attr_number] = []

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    total_created = 0
    total_failed = 0

    for attr_number in attr_numbers:
        screen_name = f"Item Attribute{attr_number}"
        results = all_results.get(attr_number, [])
        created = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))
        total_created += created
        total_failed += failed
        status_icon = "OK" if failed == 0 else "!!"
        print(f"  [{status_icon}] {screen_name:<20} {created:>3}/{count} created")

    print("-" * 70)
    print(f"  Total: {total_created} created, {total_failed} failed out of {count * len(attr_numbers)}")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()
