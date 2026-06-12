#!/usr/bin/env python3
"""
FK Discovery Tool — Resolves ALL FK IDs needed by the 7 remaining Common Settings screens.

Run this FIRST before batch_create. It discovers and caches all dropdown IDs
so that batch_create scripts can use them.

Usage:
    python fk_discovery.py
    (Paste your token when prompted)

Output:
    Saves to pages/common_settings/data/discovered/fk_cache.json
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient

SCREENS_TO_DISCOVER = [
    # Screen name variations to try (in order of likelihood)
    ("Error Code Type",  ["Error Code Type", "Error Code", "ErrorCodeType", "Error Code Master"]),
    ("HSN SAC Type",     ["HSN SAC Type", "HSN Type", "SAC Type", "HSN/SAC Type", "HSN SAC"]),
    ("Tax Type",         ["Tax Type", "TaxType"]),
    ("Country",          ["Country"]),
    ("Vehicle Type",     ["Vehicle Type", "Vehicle Category", "Vehicle Master Type", "VehicleType"]),
    ("Fuel Type",        ["Fuel Type", "Fuel Type Master", "Fuel Category", "FuelType"]),
    ("Account Type",     ["Account Type", "AccountType"]),
    ("Account",          ["Account", "Chart of Account", "Account Reference", "Account Ref", "Ledger", "Ledger Account"]),
    ("Tax Authority",    ["Tax Authority"]),
    ("UOM",              ["UOM"]),
    ("UOM Code",         ["UOM Code", "UOMCode"]),
]

CACHE_DIR = Path(PROJECT_ROOT) / "pages" / "common_settings" / "data" / "discovered"
CACHE_FILE = CACHE_DIR / "fk_cache.json"


def resolve_screen(api, display_name, attempts):
    """Try multiple screen name variations to resolve FK IDs."""
    for attempt in attempts:
        try:
            data = api.list_entries(attempt, page_size=200)
            items = data.get("screenmatlistingdata_set", [])
            if not items:
                continue

            # Try to extract {display_name: id} pairs
            result = {}
            for item in items:
                item_id = item.get("id")
                name = (item.get("name")
                        or item.get("uom_description")
                        or item.get("uom_code")
                        or item.get("tax_name")
                        or item.get("bank_name")
                        or item.get("code")
                        or str(item_id))
                if item_id is not None:
                    result[str(name)] = int(item_id)

            if result:
                return attempt, result

        except Exception as e:
            continue

    return None, {}


def parse_args():
    parser = argparse.ArgumentParser(description="Discover FK IDs for Common Settings screens")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
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
    return args


def main():
    args = parse_args()
    args = prompt_missing_args(args)

    print("=" * 70)
    print("  FK DISCOVERY TOOL — Common Settings")
    print("=" * 70)
    print()
    print(f"  Resolving FK IDs for {len(SCREENS_TO_DISCOVER)} screen types")
    print(f"  Cache: {CACHE_FILE}")
    print()

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # Load existing cache
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
            print(f"  Loaded existing cache with {len(cache)} screens")
        except:
            pass

    # ── Discover each screen type ─────────────────────────────────────
    print()
    print("-" * 70)
    print(f"  {'Screen':<25} {'Attempt':<30} {'Count':>7}")
    print("-" * 70)

    discovered = {}
    for display_name, attempts in SCREENS_TO_DISCOVER:
        matched_screen, ids = resolve_screen(api, display_name, attempts)
        if ids:
            print(f"  {display_name:<25} {matched_screen:<30} {len(ids):>7}")
            discovered[display_name] = ids
            # Also save under each attempt name for flexibility
            for alt_name in attempts:
                discovered[alt_name] = ids
        else:
            print(f"  {display_name:<25} {'NOT FOUND':<30} {0:>7}")

    # ── Also try schema-based discovery ───────────────────────────────
    print()
    print("  Trying schema-based FK discovery for the 7 target screens...")

    TARGET_SCREENS = [
        "Error Code Mst", "HSN SAC", "Tax Authority", "Vehicle Master",
        "Bank", "Tax Rate", "UOM Conversion",
    ]

    for screen_name in TARGET_SCREENS:
        try:
            schema = api.discover_structure(screen_name)
            if schema:
                print(f"    {screen_name}: Schema discovered OK")
                # Save schema for reference
                schema_file = CACHE_DIR / f"{screen_name.replace(' ', '_').lower()}_schema.json"
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                schema_file.write_text(json.dumps(schema, indent=2, default=str))
        except Exception as e:
            print(f"    {screen_name}: Schema query failed ({e})")

    # ── Save cache ────────────────────────────────────────────────────
    # Merge with existing cache
    cache.update(discovered)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    found = sum(1 for v in discovered.values() if v)
    total = len(SCREENS_TO_DISCOVER)
    print(f"  Screens resolved: {found}/{total}")
    print(f"  Cache saved to:   {CACHE_FILE}")
    print()

    # Show critical IDs for each of the 7 target screens
    print("  ── Key FK IDs by Target Screen ──")
    print()

    if "Tax Type" in discovered:
        print(f"  Tax Authority/Tax Rate → tax_type_ref_id:")
        for name, fid in list(discovered["Tax Type"].items())[:5]:
            print(f"    {name}: {fid}")

    if "Country" in discovered:
        print(f"  Tax Authority → country_ref_id:")
        for name, fid in list(discovered["Country"].items())[:3]:
            print(f"    {name}: {fid}")

    if "Vehicle Type" in discovered:
        print(f"  Vehicle Master → vehicle_type_id:")
        for name, fid in list(discovered["Vehicle Type"].items())[:5]:
            print(f"    {name}: {fid}")

    if "Fuel Type" in discovered:
        print(f"  Vehicle Master → fuel_type_ref_id:")
        for name, fid in list(discovered["Fuel Type"].items())[:5]:
            print(f"    {name}: {fid}")

    if "Account Type" in discovered:
        print(f"  Bank → account_type:")
        for name, fid in list(discovered["Account Type"].items())[:5]:
            print(f"    {name}: {fid}")

    if "UOM" in discovered:
        print(f"  UOM Conversion → source/target_uom_code:")
        for name, fid in list(discovered["UOM"].items())[:8]:
            print(f"    {name}: {fid}")
        if len(discovered["UOM"]) > 8:
            print(f"    ... and {len(discovered['UOM']) - 8} more")

    print()
    print("  Next step: Run batch_create.py for each module")
    api.close()


if __name__ == "__main__":
    main()
