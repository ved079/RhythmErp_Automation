#!/usr/bin/env python3
"""
harvest_chains.py
-----------------
Extract address chains from existing Supplier entries in the ERP.
Reads all entries via the API, extracts state/district/taluka/village FK IDs,
and prints deduplicated chains to paste into _ADDRESS_CHAINS.

Usage:
    python pages/registration/modules/supplier/scripts/harvest_chains.py --token eyJhbGci...
"""

import sys
import os
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


def harvest_address_chains(client: RhythmERPAPIClient) -> list:
    """Read all Supplier entries and extract unique address chains."""
    all_chains = []
    seen = set()
    page = 1
    page_size = 50
    total_entries = 0

    while True:
        log.info(f"[Harvest] Fetching page {page}...")
        result = client.list_entries("Supplier", page=page, page_size=page_size)

        if not result:
            log.warning("[Harvest] No more entries or API error")
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

                    chain = {
                        "state_ref_id_id": state,
                        "district_ref_id_id": district,
                        "sub_district_ref_id_id": taluka,
                        "village_ref_id_id": village,
                    }
                    all_chains.append(chain)

        total_in_db = result.get("count", 0)
        if total_entries >= total_in_db:
            break

        page += 1

    log.info(f"[Harvest] Scanned {total_entries} entries, found {len(all_chains)} unique chains")
    return all_chains


def main():
    token = None
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            break

    client = RhythmERPAPIClient()

    if token:
        client.login_from_browser(token=token, tenant_id="599")
    else:
        print("=" * 60)
        print("USAGE: python harvest_chains.py --token <YOUR_TOKEN>")
        print("")
        print("Get your token from DevTools -> Network -> any /core/ request")
        print("=" * 60)
        sys.exit(1)

    chains = harvest_address_chains(client)
    client.close()

    if not chains:
        print("\nNo address chains found!")
        return

    states = set(c["state_ref_id_id"] for c in chains)
    districts = set(c["district_ref_id_id"] for c in chains)
    talukas = set(c["sub_district_ref_id_id"] for c in chains)

    print(f"\n{'=' * 60}")
    print(f"ADDRESS CHAIN HARVEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Total unique chains: {len(chains)}")
    print(f"  Unique states:    {len(states)}  -> {sorted(states)}")
    print(f"  Unique districts: {len(districts)}  -> {sorted(districts)}")
    print(f"  Unique talukas:   {len(talukas)}")

    print(f"\n{'=' * 60}")
    print(f"PASTE THIS INTO _ADDRESS_CHAINS in supplier_data.py:")
    print(f"{'=' * 60}")

    from collections import defaultdict
    by_state = defaultdict(list)
    for chain in chains:
        by_state[chain["state_ref_id_id"]].append(chain)

    for state_id in sorted(by_state.keys()):
        state_chains = by_state[state_id]
        print(f"    # -- State ID {state_id} ({len(state_chains)} chain(s)) --")
        for chain in state_chains:
            v = chain["village_ref_id_id"]
            v_str = str(v) if v is not None else "None"
            print(f'    {{"state_ref_id_id": {chain["state_ref_id_id"]}, "district_ref_id_id": {chain["district_ref_id_id"]}, "sub_district_ref_id_id": {chain["sub_district_ref_id_id"]}, "village_ref_id_id": {v_str}, "_verified": True}},')

    # Also save to JSON
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "harvested_chains.json")
    with open(output_path, "w") as f:
        json.dump(chains, f, indent=2)
    print(f"\nChains also saved to: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
