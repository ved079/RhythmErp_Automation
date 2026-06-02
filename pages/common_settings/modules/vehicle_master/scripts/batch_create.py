#!/usr/bin/env python3
"""
Vehicle Master — Batch Create

Screen: "Vehicle Master" (flat, 2 FK dropdowns: vehicle_type_id, fuel_type_ref_id)
Auto-discovers FK IDs at startup.
"""

import sys
import os
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_vehicle_master_api_payloads,
)

SCREEN_NAME = "Vehicle Master"


def main():
    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs...")
    resolver = FkResolver(api)

    # Vehicle Type — try multiple names
    vt_ids = {}
    for attempt in ["Vehicle Type", "Vehicle Category", "Vehicle Master Type"]:
        vt_ids = resolver.resolve(attempt)
        if vt_ids:
            print(f"    vehicle_type_id: Found {len(vt_ids)} values from '{attempt}'")
            break
    if not vt_ids:
        print("    vehicle_type_id: NOT FOUND — will use placeholder IDs")

    # Fuel Type
    ft_ids = {}
    for attempt in ["Fuel Type", "Fuel Type Master", "Fuel Category"]:
        ft_ids = resolver.resolve(attempt)
        if ft_ids:
            print(f"    fuel_type_ref_id: Found {len(ft_ids)} values from '{attempt}'")
            break
    if not ft_ids:
        print("    fuel_type_ref_id: NOT FOUND — will use placeholder IDs")

    fk_ids = {
        "vehicle_type_id": vt_ids,
        "fuel_type_ref_id": ft_ids,
    }

    # ── Generate payloads ─────────────────────────────────────────────
    count = 10
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_vehicle_master_api_payloads(count=count, fk_ids=fk_ids)

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
