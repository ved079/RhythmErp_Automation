#!/usr/bin/env python3
"""
capture_cascade.py
------------------
One-time helper to expand the address chain pool.

When you capture an encrypted query from DevTools, this script
calls it and shows the results. You can then add new chains to
the pool in supplier_data.py.

Usage:
    python scripts/capture_cascade.py

Workflow:
    1. Open Supplier create form in browser → Address step
    2. Select India, then select a state
    3. Open DevTools → Network tab → click District dropdown
    4. Right-click the /core/execute-query/ request → Copy URL
    5. Paste it below → script calls it and shows districts
    6. Pick a district, capture taluka query, paste it
    7. Pick a taluka, capture village query, paste it
    8. Script prints the complete chain to add to _ADDRESS_CHAINS
"""

import os
import sys
import json
import urllib.parse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwMzQyNDIxLCJpYXQiOjE3ODAzMjgwMjEsImp0aSI6ImM2Zjc5ZjAwOGIwODQxNDRiMzQyMGRiMzg3YmU2N2E2IiwidXNlcl9pZCI6IjE0NiJ9.qFjlwOlQWhbVFGoQSvuy8FWkEnoKo92qtvJ6fCpkd3Y"
TENANT_ID = "599"

# State ID lookup (from schema filter_dropdown_raw_query + existing data)
STATE_NAMES = {
    82: "Punjab",
    12: "Maharashtra",
    # Add more as you discover them
}


def call_encrypted_query(client, url_or_query):
    """Call /core/execute-query/ with an encrypted query string.

    Args:
        url_or_query: Either a full URL or just the encrypted query string.
    """
    # Extract just the query param if full URL provided
    if "execute-query" in url_or_query:
        parsed = urllib.parse.urlparse(url_or_query)
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("query", [""])[0]
    else:
        query = url_or_query

    if not query:
        print("  ERROR: No query string found in the URL")
        return []

    resp = client.session.get(
        f"{client.BASE_URL}/core/execute-query/",
        params={"query": query},
        timeout=15,
    )

    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            return data
        else:
            print(f"  Unexpected response format: {type(data)}")
            return []
    else:
        print(f"  ERROR: Status {resp.status_code}")
        return []


def main():
    client = RhythmERPAPIClient()
    client.login_from_browser(token=TOKEN, tenant_id=TENANT_ID)

    print("=" * 70)
    print("CASCADE ADDRESS CAPTURE TOOL")
    print("=" * 70)
    print()
    print("This tool helps you capture valid address chains from DevTools.")
    print("For each level, paste the encrypted query URL from the Network tab.")
    print()

    # ── Step 1: State query (optional — we may already know the state) ──
    state_id = input("Enter STATE ID (e.g., 12=Maharashtra, 82=Punjab) or press Enter to capture: ").strip()
    if not state_id:
        print("\nPaste the STATE dropdown URL from DevTools (after selecting India):")
        state_url = input("URL: ").strip()
        if state_url:
            states = call_encrypted_query(client, state_url)
            if states:
                print(f"\n  Found {len(states)} states:")
                for s in states:
                    STATE_NAMES[s['id']] = s['key']
                    print(f"    ID={s['id']}, Name={s['key']}")
                state_id = input("\n  Pick a state ID: ").strip()
            else:
                print("  No states found. Check the URL.")
                client.close()
                return

    state_id = int(state_id)
    state_name = STATE_NAMES.get(state_id, f"State {state_id}")
    print(f"\n  Selected: {state_name} (ID={state_id})")

    # ── Step 2: District query ──
    print(f"\nNow in the browser, select {state_name} and click the District dropdown.")
    print("Capture the /core/execute-query/ URL from DevTools and paste below:")
    district_url = input("URL: ").strip()
    if not district_url:
        print("No URL provided. Exiting.")
        client.close()
        return

    districts = call_encrypted_query(client, district_url)
    if not districts:
        print("No districts found. Check the URL.")
        client.close()
        return

    print(f"\n  Found {len(districts)} districts:")
    for d in districts[:15]:
        print(f"    ID={d['id']}, Name={d['key']}")
    if len(districts) > 15:
        print(f"    ... and {len(districts)-15} more")

    district_id = input("\n  Pick a district ID: ").strip()
    district_id = int(district_id)
    district_name = next((d['key'] for d in districts if d['id'] == district_id), f"District {district_id}")
    print(f"  Selected: {district_name} (ID={district_id})")

    # ── Step 3: Taluka query ──
    print(f"\nNow select {district_name} and click the Taluka dropdown.")
    print("Capture the URL and paste below:")
    taluka_url = input("URL: ").strip()
    if not taluka_url:
        print("No URL provided. Exiting.")
        client.close()
        return

    talukas = call_encrypted_query(client, taluka_url)
    if not talukas:
        print("No talukas found. Check the URL.")
        client.close()
        return

    print(f"\n  Found {len(talukas)} talukas:")
    for t in talukas[:15]:
        print(f"    ID={t['id']}, Name={t['key']}")
    if len(talukas) > 15:
        print(f"    ... and {len(talukas)-15} more")

    taluka_id = input("\n  Pick a taluka ID: ").strip()
    taluka_id = int(taluka_id)
    taluka_name = next((t['key'] for t in talukas if t['id'] == taluka_id), f"Taluka {taluka_id}")
    print(f"  Selected: {taluka_name} (ID={taluka_id})")

    # ── Step 4: Village query (optional) ──
    village_id = None
    print(f"\nNow select {taluka_name} and click the Village dropdown.")
    print("Capture the URL and paste below (or press Enter to skip):")
    village_url = input("URL: ").strip()

    if village_url:
        villages = call_encrypted_query(client, village_url)
        if villages:
            print(f"\n  Found {len(villages)} villages:")
            for v in villages[:15]:
                print(f"    ID={v['id']}, Name={v['key']}")
            if len(villages) > 15:
                print(f"    ... and {len(villages)-15} more")

            village_input = input("\n  Pick a village ID (or Enter to skip): ").strip()
            if village_input:
                village_id = int(village_input)
                village_name = next((v['key'] for v in villages if v['id'] == village_id), f"Village {village_id}")
                print(f"  Selected: {village_name} (ID={village_id})")

    # ── Print the chain to add ──
    print("\n" + "=" * 70)
    print("ADD THIS CHAIN TO _ADDRESS_CHAINS in supplier_data.py:")
    print("=" * 70)
    chain = {
        "state_ref_id_id": state_id,
        "district_ref_id_id": district_id,
        "sub_district_ref_id_id": taluka_id,
    }
    if village_id:
        chain["village_ref_id_id"] = village_id

    chain_str = json.dumps(chain, indent=4)
    # Add comment with names
    print(f"    # ── {state_name} / {district_name} / {taluka_name} {'/ '+village_name if village_id else ''} ──")
    print(f"    {chain_str},")

    print("\nDone!")
    client.close()


if __name__ == "__main__":
    main()
