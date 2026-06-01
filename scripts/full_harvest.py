#!/usr/bin/env python3
"""
Full harvest of ALL Supplier entries to extract verified address chains.
Paginates through every page, extracts unique state/district/taluka/village chains.
"""

import sys
import json
import time

sys.path.insert(0, '/home/z/my-project/RhythmErp_Automation')

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwMzQyNDIxLCJpYXQiOjE3ODAzMjgwMjEsImp0aSI6ImM2Zjc5ZjAwOGIwODQxNDRiMzQyMGRiMzg3YmU2N2E2IiwidXNlcl9pZCI6IjE0NiJ9.qFjlwOlQWhbVFGoQSvuy8FWkEnoKo92qtvJ6fCpkd3Y"
TENANT_ID = "599"


def main():
    client = RhythmERPAPIClient()
    client.login_from_browser(token=TOKEN, tenant_id=TENANT_ID)

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

    print(f"\n{'='*60}")
    print(f"FULL HARVEST RESULTS")
    print(f"{'='*60}")
    print(f"Scanned: {total_entries} entries ({errors} errors)")
    print(f"Unique chains: {len(all_chains)}")
    print(f"Unique states: {len(states)} -> {sorted(states)}")
    print(f"Unique districts: {len(districts)} -> {sorted(districts)}")

    # Group and print Python code
    from collections import defaultdict
    by_state = defaultdict(list)
    for chain in all_chains:
        by_state[chain["state_ref_id_id"]].append(chain)

    print(f"\n{'='*60}")
    print("PASTE INTO _ADDRESS_CHAINS:")
    print(f"{'='*60}")

    for state_id in sorted(by_state.keys()):
        state_chains = by_state[state_id]
        print(f"    # State ID {state_id} ({len(state_chains)} chain(s))")
        for chain in state_chains:
            v = chain["village_ref_id_id"]
            v_str = str(v) if v is not None else "None"
            print(f'    {{"state_ref_id_id": {chain["state_ref_id_id"]}, "district_ref_id_id": {chain["district_ref_id_id"]}, "sub_district_ref_id_id": {chain["sub_district_ref_id_id"]}, "village_ref_id_id": {v_str}, "_verified": True}},')

    print(f"\n{'='*60}")

    # Also save to JSON for programmatic use
    output_path = "/home/z/my-project/RhythmErp_Automation/scripts/harvested_chains.json"
    with open(output_path, "w") as f:
        json.dump(all_chains, f, indent=2)
    print(f"Chains also saved to: {output_path}")


if __name__ == "__main__":
    main()
