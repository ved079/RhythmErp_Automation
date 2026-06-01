#!/usr/bin/env python3
"""
batch_create.py
---------------
Main runner: create multiple UOM Conversion entries via API with randomized data.

Uses realistic Indian agricultural/commodity conversion pairs with proper
factors (e.g., KG to Gram = 1000, Acre to Hectare = 0.4047, Maund to KG = 37.3242).

IMPORTANT: UOM Conversion depends on UOM entries already existing in the system.
Make sure you have created UOM entries (KG, Gram, Metre, Litre, etc.) before
running this script. The source_uom_ref_id and target_uom_ref_id must reference
valid UOM master entries.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/uom_conversion/scripts/batch_create.py
    python pages/common_settings/modules/uom_conversion/scripts/batch_create.py --count 10
    python pages/common_settings/modules/uom_conversion/scripts/batch_create.py --token eyJhbGci...
    python pages/common_settings/modules/uom_conversion/scripts/batch_create.py --dry-run
"""

import sys
import os
import time

# Add project root to path (uom_conversion/scripts -> uom_conversion -> modules -> common_settings -> pages -> project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_api_payload,
    UOM_IDS,
    REALISTIC_UOM_CONVERSION_PAIRS,
)

TENANT_ID = "599"
DEFAULT_COUNT = 10
SCREEN_NAME = "UOM Conversion"


def parse_args():
    args = {"token": None, "count": DEFAULT_COUNT, "dry_run": False}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--token" and i + 1 < len(sys.argv):
            args["token"] = sys.argv[i + 1]
            i += 2
        elif arg == "--count" and i + 1 < len(sys.argv):
            args["count"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--dry-run":
            args["dry_run"] = True
            i += 1
        else:
            i += 1
    return args


def check_uom_dependency(client):
    """Check if UOM entries exist in the system before creating conversions.

    Returns:
        dict mapping UOM name -> ref_id if found, empty dict otherwise.
    """
    try:
        result = client.list_entries("UOM", page=1, page_size=100)
        if not result:
            print("  WARNING: Could not verify UOM entries. Proceeding anyway.")
            return {}

        items = result.get("screenmatlistingdata_set", [])
        if not items:
            print("  WARNING: No UOM entries found in the system!")
            print("  UOM Conversion requires UOM entries (KG, Gram, Metre, etc.) to exist first.")
            print("  Create UOM entries before running this script.")
            return {}

        # Build a name -> id mapping from existing UOM entries
        uom_map = {}
        for item in items:
            name = item.get("name", "")
            uid = item.get("id")
            if name and uid:
                uom_map[name] = uid

        print(f"  Found {len(uom_map)} UOM entries: {sorted(uom_map.keys())}")
        return uom_map

    except Exception as e:
        print(f"  WARNING: Could not verify UOM entries: {e}")
        return {}


def batch_create(client, count, dry_run=False, uom_ids=None):
    success = 0
    fail = 0
    pairs_used = []
    start = time.time()

    print("=" * 70)
    print(f"  UOM CONVERSION BATCH CREATE — {count} entries")
    print("=" * 70)

    # Build dropdown_ids with uom_ids
    dropdown_ids = {}
    if uom_ids:
        dropdown_ids["uom_ids"] = uom_ids

    for i in range(count):
        payload = generate_uom_conversion_api_payload(dropdown_ids=dropdown_ids or None)
        source_id = payload.get("source_uom_ref_id")
        target_id = payload.get("target_uom_ref_id")
        factor = payload.get("conversion_factor", "?")

        # Find source/target names for display
        source_name = "?"
        target_name = "?"
        if uom_ids:
            for name, rid in uom_ids.items():
                if rid == source_id:
                    source_name = name
                if rid == target_id:
                    target_name = name

        pairs_used.append((source_name, target_name, factor))

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {source_name:15s} -> {target_name:15s} × {factor:12.4f}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            rid = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {source_name:15s} -> {target_name:15s} × {factor:12.4f} | ID={rid}")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {source_name:15s} -> {target_name:15s} × {factor:12.4f}")
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created:     {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:        {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    if pairs_used:
        unique_sources = set(p[0] for p in pairs_used)
        unique_targets = set(p[1] for p in pairs_used)
        print(f"  Source UOMs:  {sorted(unique_sources)} ({len(unique_sources)} unique)")
        print(f"  Target UOMs: {sorted(unique_targets)} ({len(unique_targets)} unique)")
    print(f"  Available pairs: {len(REALISTIC_UOM_CONVERSION_PAIRS)} realistic Indian conversions")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  UOM CONVERSION BATCH CREATE")
        print("=" * 70)
        print()
        print("  No token provided. Get it from:")
        print("  1. Open https://rhythmerp.algorhythms.in in Chrome")
        print("  2. DevTools -> Network -> click any page")
        print("  3. Find any /core/ request -> copy Authorization header")
        print("  4. Paste the token value (after 'Bearer ')")
        print()
        token = input("  Token: ").strip()
        if not token:
            print("  No token entered. Exiting.")
            return

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)

    # Validate token with a list_entries call
    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    # Show existing count
    existing = result.get("screenmatlistingdata_set", [])
    total_count = result.get("count", len(existing))
    print(f"  Existing UOM Conversion entries: {total_count}")
    print()

    # Check UOM dependency
    print("  Checking UOM entries (dependency)...")
    uom_ids = check_uom_dependency(client)
    if not uom_ids:
        print()
        print("  ⚠  WARNING: No UOM entries found or could not be verified.")
        print("  ⚠  UOM Conversion requires UOM entries to exist first.")
        print("  ⚠  Source/Target UOM ref IDs will be None — API calls will likely fail.")
        print()
        proceed = input("  Continue anyway? (y/N): ").strip().lower()
        if proceed != "y":
            print("  Exiting. Create UOM entries first, then re-run.")
            client.close()
            return
    print()

    batch_create(client, count, dry_run, uom_ids=uom_ids)
    client.close()


if __name__ == "__main__":
    main()
