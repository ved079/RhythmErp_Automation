"""
harvest_addresses.py
--------------------
Extract address chains from existing Supplier entries in the ERP.

Reads all existing Supplier entries via the API, extracts their
state/district/taluka/village FK IDs, and prints deduplicated
address chains that can be pasted into _ADDRESS_CHAINS in
supplier_data.py.

Also prints the pool expansion stats (how many unique states,
districts, etc. were found).

Usage:
    python scripts/harvest_addresses.py

    # Or with a custom token:
    python scripts/harvest_addresses.py --token eyJhbGci...
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


def harvest_address_chains(client: RhythmERPAPIClient) -> list:
    """
    Read all Supplier entries and extract unique address chains.

    Returns a list of dicts with:
        state_ref_id_id, district_ref_id_id,
        sub_district_ref_id_id, village_ref_id_id
    """
    all_chains = []
    seen = set()

    # Paginate through all entries
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

            # Get detailed entry
            detail = client.get_entry("Supplier", entry_id)
            if not detail:
                continue

            # Find Address Details stepper in children
            children = detail.get("children", [])
            for child in children:
                if child.get("stepper_name") != "Address Details":
                    continue

                for addr in child.get("details", []):
                    state = addr.get("state_ref_id_id")
                    district = addr.get("district_ref_id_id")
                    taluka = addr.get("sub_district_ref_id_id")
                    village = addr.get("village_ref_id_id")

                    if state is None:
                        continue  # Skip entries without proper address

                    # Create a hashable key for deduplication
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

        # Check if there are more pages
        total_in_db = result.get("count", 0)
        if total_entries >= total_in_db:
            break

        page += 1

    log.info(f"[Harvest] Scanned {total_entries} entries, found {len(all_chains)} unique chains")
    return all_chains


def main():
    # Use token from command line or the hardcoded one
    token = None
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            break

    client = RhythmERPAPIClient()

    if token:
        client.login_from_browser(token=token, tenant_id="599")
    else:
        # Try to use the last known token
        # User should replace this with their current token from DevTools
        print("=" * 60)
        print("USAGE: python scripts/harvest_addresses.py --token <YOUR_TOKEN>")
        print("")
        print("Get your token from DevTools → Network → any /core/ request")
        print("Copy the Authorization header value (after 'Bearer ')")
        print("=" * 60)
        sys.exit(1)

    chains = harvest_address_chains(client)
    client.close()

    if not chains:
        print("\nNo address chains found!")
        return

    # Print stats
    states = set(c["state_ref_id_id"] for c in chains)
    districts = set(c["district_ref_id_id"] for c in chains)
    talukas = set(c["sub_district_ref_id_id"] for c in chains)
    villages = set(c["village_ref_id_id"] for c in chains)

    print(f"\n{'=' * 60}")
    print(f"ADDRESS CHAIN HARVEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Total unique chains: {len(chains)}")
    print(f"  Unique states:    {len(states)}  → {sorted(states)}")
    print(f"  Unique districts: {len(districts)}  → {sorted(districts)}")
    print(f"  Unique talukas:   {len(talukas)}  → {sorted(talukas)}")
    print(f"  Unique villages:  {len(villages)}")

    # Print Python code to paste into supplier_data.py
    print(f"\n{'=' * 60}")
    print(f"PASTE THIS INTO _ADDRESS_CHAINS in supplier_data.py:")
    print(f"{'=' * 60}")

    # Group by state for readability
    from collections import defaultdict
    by_state = defaultdict(list)
    for chain in chains:
        by_state[chain["state_ref_id_id"]].append(chain)

    for state_id in sorted(by_state.keys()):
        state_chains = by_state[state_id]
        print(f"    # ── State ID {state_id} ({len(state_chains)} chain(s)) ──")
        for chain in state_chains:
            print(f"    {{")
            print(f"        \"state_ref_id_id\": {chain['state_ref_id_id']},")
            print(f"        \"district_ref_id_id\": {chain['district_ref_id_id']},")
            print(f"        \"sub_district_ref_id_id\": {chain['sub_district_ref_id_id']},")
            print(f"        \"village_ref_id_id\": {chain['village_ref_id_id']},")
            print(f"    }},")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
