#!/usr/bin/env python3
"""
test_cascade_query.py
---------------------
Test if /core/execute-query/ accepts substituted (but unencrypted) SQL.
If yes, we can build a dynamic cascade resolver.
If no, we'll use the pool approach.

Usage:
    python scripts/test_cascade_query.py
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


def main():
    client = RhythmERPAPIClient()
    client.login_from_browser(token=TOKEN, tenant_id=TENANT_ID)

    base_url = client.BASE_URL

    # ── Test 1: Substituted SQL for State dropdown (India=8) ──
    state_sql = "SELECT id,state_name as key FROM dynamic_models_state_mst WHERE is_deleted=false AND is_active=true and country_code=8 ;"

    print("=" * 70)
    print("TEST 1: Substituted SQL → /core/execute-query/")
    print("=" * 70)
    print(f"SQL: {state_sql}\n")

    resp = client.session.get(
        f"{base_url}/core/execute-query/",
        params={"query": state_sql},
        timeout=15,
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"SUCCESS! Got {len(data) if isinstance(data, list) else '?'} states")
        for item in data[:10]:
            print(f"  {item}")
        if isinstance(data, list) and len(data) > 10:
            print(f"  ... and {len(data)-10} more")
    else:
        print(f"FAILED: {resp.text[:300]}")

    # ── Test 2: Try with URL-encoded SQL as the query param ──
    print("\n" + "=" * 70)
    print("TEST 2: Same but double-check encoding")
    print("=" * 70)

    resp2 = client.session.get(
        f"{base_url}/core/execute-query/?query={urllib.parse.quote(state_sql, safe='')}",
        timeout=15,
    )
    print(f"Status: {resp2.status_code}")
    if resp2.status_code == 200:
        data2 = resp2.json()
        print(f"SUCCESS! Got {len(data2) if isinstance(data2, list) else '?'} states")
    else:
        print(f"FAILED: {resp2.text[:300]}")

    # ── Test 3: Try the encrypted query string the user captured ──
    # This is the Maharashtra district query the user captured
    print("\n" + "=" * 70)
    print("TEST 3: Replay the encrypted query user captured (Maharashtra districts)")
    print("=" * 70)

    encrypted_maha_districts = "AoDiOUZ3QTZpRiug1igd2LJ5ZE8ReeQwe7blDbv0SjZhonpbwDaCWkfsYimDKxx8ENByLCKdaohYKh/0pRNtMKN2RsqPeYyK0/eyi6J5Z9iDldrTnJhgDbrZOQ2qfDEGPyJKXtiX2EP1O5K+qG/rV2OxlaHhYtaCeszSPze7O4jQrhokJgtFPwVncodGsZHy"

    resp3 = client.session.get(
        f"{base_url}/core/execute-query/",
        params={"query": encrypted_maha_districts},
        timeout=15,
    )
    print(f"Status: {resp3.status_code}")
    if resp3.status_code == 200:
        data3 = resp3.json()
        print(f"SUCCESS! Got {len(data3)} districts for Maharashtra")
        for item in data3[:5]:
            print(f"  {item}")
    else:
        print(f"FAILED: {resp3.text[:300]}")

    # ── Test 4: Try state dropdown via the screen schema with parent param ──
    print("\n" + "=" * 70)
    print("TEST 4: Schema with parent param (experimental)")
    print("=" * 70)

    resp4 = client.session.get(
        f"{base_url}/core/dynamic-screen/Supplier/",
        params={"country_ref_id_id": 8},
        timeout=15,
    )
    print(f"Status: {resp4.status_code}")
    if resp4.status_code == 200:
        schema = resp4.json()
        all_fields = client._flatten_fields(schema.get("screendefinition_set", []))
        for field in all_fields:
            if field.get("field_key") == "state_ref_id_id":
                fdrq = field.get("filter_dropdown_raw_query", [])
                print(f"State filter_dropdown_raw_query: {len(fdrq) if isinstance(fdrq, list) else fdrq}")
                if isinstance(fdrq, list) and fdrq:
                    for item in fdrq[:5]:
                        print(f"  {item}")
                break

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
