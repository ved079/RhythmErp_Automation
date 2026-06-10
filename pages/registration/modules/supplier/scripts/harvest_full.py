#!/usr/bin/env python3
"""
harvest_full.py
---------------
Full pagination harvest of ALL Supplier entries to extract verified address chains.
More thorough than harvest_chains.py — scans every page.

Usage:
    python pages/registration/modules/supplier/scripts/harvest_full.py --token eyJhbGci...
"""

import sys
import os
import json
import time

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


def main():
    token = None
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            break

    if not token:
        print("=" * 60)
        print("USAGE: python harvest_full.py --token <YOUR_TOKEN>")
        print("=" * 60)
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id="681")

    all_chains = []
    seen = set()
    total_entries = 0
    page = 1
    errors = 0

    while True:
        log.info(f"Fetching page {page}...")
        result = client.list_entries("Supplier", page=page, page_size=50)
        if not result:
            break

        items = result.get("screenmatlistingdata_set", [])
        if not items:
            break

        total_entries += len(items)

        for item in items:
            entry_id = item.get("id")
            if not entry_id:
                continue

            detail = client.get_entry("Supplier", entry_id)
            if not detail:
                errors += 1
                continue

            for child in detail.get("children", []):
                if child.get("stepper_name") != "Address Details":
                    continue

                for addr in child.get("details", []):
                    state = addr.get("state_ref_id_id")
                    district = addr.get("district_ref_id_id")
                    taluka = addr.get("sub_district_ref_id_id")
                    village = addr.get("village_ref_id_id")

                    if state is None:
                        continue

                    key = (state, district, taluka, village)
                    if key in seen:
                        continue
                    seen.add(key)

                    all_chains.append({
                        "state_ref_id_id": state,
                        "district_ref_id_id": district,
                        "sub_district_ref_id_id": taluka,
                        "village_ref_id_id": village,
                    })

        page += 1
        time.sleep(0.2)

    client.close()

    # Stats
    states = set(c["state_ref_id_id"] for c in all_chains)
    districts = set(c["district_ref_id_id"] for c in all_chains)

    print(f"\n{'=' * 60}")
    print(f"FULL HARVEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Scanned: {total_entries} entries ({errors} errors)")
    print(f"Unique chains: {len(all_chains)}")
    print(f"Unique states: {len(states)} -> {sorted(states)}")
    print(f"Unique districts: {len(districts)} -> {sorted(districts)}")

    # Group and print Python code
    from collections import defaultdict
    by_state = defaultdict(list)
    for chain in all_chains:
        by_state[chain["state_ref_id_id"]].append(chain)

    print(f"\n{'=' * 60}")
    print("PASTE INTO _ADDRESS_CHAINS:")
    print(f"{'=' * 60}")

    for state_id in sorted(by_state.keys()):
        state_chains = by_state[state_id]
        print(f"    # State ID {state_id} ({len(state_chains)} chain(s))")
        for chain in state_chains:
            v = chain["village_ref_id_id"]
            v_str = str(v) if v is not None else "None"
            print(f'    {{"state_ref_id_id": {chain["state_ref_id_id"]}, "district_ref_id_id": {chain["district_ref_id_id"]}, "sub_district_ref_id_id": {chain["sub_district_ref_id_id"]}, "village_ref_id_id": {v_str}, "_verified": True}},')

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "harvested_chains.json")
    with open(output_path, "w") as f:
        json.dump(all_chains, f, indent=2)
    print(f"\nChains also saved to: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
